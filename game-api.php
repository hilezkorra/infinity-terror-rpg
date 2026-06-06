<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { exit; }

$action = $_GET['action'] ?? ($_POST['action'] ?? '');
$base   = __DIR__;

// ── Helper functions ───────────────────────────────────────
function readJson($path) {
    if (!file_exists($path)) return null;
    return json_decode(file_get_contents($path), true);
}
function writeJson($path, $data) {
    $dir = dirname($path);
    if (!is_dir($dir)) mkdir($dir, 0777, true);
    file_put_contents($path, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}
function nextMsgId($chat) {
    if (empty($chat['messages'])) return 1;
    return max(array_column($chat['messages'], 'id')) + 1;
}

// ── Get game state ─────────────────────────────────────────
if ($action === 'get-state') {
    $game = readJson($base . '/data/game.json');
    echo json_encode($game ?: ['error' => 'No game state found']);
    exit;
}

// ── Get chat ──────────────────────────────────────────────
if ($action === 'get-chat') {
    $chat = readJson($base . '/data/chat.json');
    echo json_encode($chat ?: ['messages' => [], 'status' => 'error']);
    exit;
}

// ── Get movies list ───────────────────────────────────────
if ($action === 'get-movies') {
    $movies = readJson($base . '/system/movies.json');
    echo json_encode($movies ?: ['error' => 'No movies found']);
    exit;
}

// ── Get sounds ────────────────────────────────────────────
if ($action === 'get-sounds') {
    $sounds = readJson($base . '/system/sounds.json');
    echo json_encode($sounds ?: ['error' => 'No sounds found']);
    exit;
}

// ── Get music ─────────────────────────────────────────────
if ($action === 'get-music') {
    $music = readJson($base . '/system/music.json');
    echo json_encode($music ?: ['error' => 'No music found']);
    exit;
}

// ── Send player command ────────────────────────────────────
if ($action === 'send-command' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $chatFile = $base . '/data/chat.json';
    $input    = json_decode(file_get_contents('php://input'), true);
    $command  = trim($input['command'] ?? '');
    if (!$command) { http_response_code(400); echo json_encode(['error' => 'No command']); exit; }
    if (!file_exists($chatFile)) { http_response_code(500); echo json_encode(['error' => 'Chat missing']); exit; }

    $chat = readJson($chatFile);
    $msg  = [
        'id'        => nextMsgId($chat),
        'sender'    => 'player',
        'content'   => $command,
        'timestamp' => date('c'),
    ];
    $chat['messages'][] = $msg;
    $chat['status']     = 'waiting_for_gm';
    writeJson($chatFile, $chat);
    echo json_encode(['ok' => true, 'message' => $msg]);
    exit;
}

// ── Save lobby state ──────────────────────────────────────
if ($action === 'save-lobby' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $game = readJson($gameFile);
    if (!$game) { http_response_code(500); echo json_encode(['error' => 'No game state']); exit; }

    $idx = ($game['lobby_save_index'] ?? 0) + 1;
    $savePath = $base . '/saves/lobby-' . $idx . '.json';

    // Save current state
    writeJson($savePath, $game);

    // Update game with new save index
    $game['lobby_save_index']  = $idx;
    $game['last_lobby_save']   = 'saves/lobby-' . $idx . '.json';
    writeJson($gameFile, $game);

    echo json_encode(['ok' => true, 'save_path' => $game['last_lobby_save'], 'index' => $idx]);
    exit;
}

// ── Restore on player death ───────────────────────────────
if ($action === 'player-died' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile  = $base . '/data/game.json';
    $chatFile  = $base . '/data/chat.json';
    $game = readJson($gameFile);
    if (!$game) { http_response_code(500); echo json_encode(['error' => 'No game state']); exit; }

    $lastSavePath = $game['last_lobby_save'] ?? null;
    if (!$lastSavePath || !file_exists($base . '/' . $lastSavePath)) {
        // No lobby save yet — soft restore to starting state
        $game['phase']            = 'lobby';
        $game['current_movie']    = null;
        $game['deaths']           = ($game['deaths'] ?? 0) + 1;
        $game['character']['hp']  = $game['character']['hp_max'] ?? 100;
        $game['character']['status_effects'] = [];
        writeJson($gameFile, $game);
        echo json_encode(['ok' => true, 'restored_from' => 'initial']);
        exit;
    }

    // Restore game from lobby save
    $savedGame = readJson($base . '/' . $lastSavePath);
    if (!$savedGame) { http_response_code(500); echo json_encode(['error' => 'Cannot read save']); exit; }

    $deaths = ($game['deaths'] ?? 0) + 1;
    $savedGame['deaths'] = $deaths;
    $savedGame['phase']  = 'lobby';
    $savedGame['current_movie'] = null;
    $savedGame['movie_start_message_id'] = null;
    writeJson($gameFile, $savedGame);

    // Trim chat back to pre-movie state
    $chat = readJson($chatFile);
    $movieStartId = $game['movie_start_message_id'] ?? null;
    if ($movieStartId && $chat) {
        $chat['messages'] = array_values(array_filter(
            $chat['messages'],
            fn($m) => ($m['id'] ?? 0) < $movieStartId
        ));
        // Add restoration message
        $chat['messages'][] = [
            'id'        => nextMsgId($chat),
            'sender'    => 'system',
            'content'   => 'CONSCIOUSNESS RESTORED — Death registered. Body reconstituted from last Lobby checkpoint. State reverted to last Lobby departure. Deaths total: ' . $deaths,
            'timestamp' => date('c'),
        ];
        $chat['status'] = 'waiting_for_gm';
        writeJson($chatFile, $chat);
    }

    echo json_encode(['ok' => true, 'restored_from' => $lastSavePath, 'deaths' => $deaths]);
    exit;
}

// ── Load a specific save file ─────────────────────────────
if ($action === 'load-save' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $chatFile = $base . '/data/chat.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $file = basename(trim($input['file'] ?? ''));
    if (!$file || !str_starts_with($file, 'lobby-') || !str_ends_with($file, '.json')) {
        http_response_code(400); echo json_encode(['error' => 'Invalid save file']); exit;
    }
    $savePath = $base . '/saves/' . $file;
    if (!file_exists($savePath)) {
        http_response_code(404); echo json_encode(['error' => 'Save file not found']); exit;
    }
    $savedGame = readJson($savePath);
    if (!$savedGame) {
        http_response_code(500); echo json_encode(['error' => 'Cannot read save file']); exit;
    }
    // Restore — same logic as player-died but from a chosen save
    $game = readJson($gameFile);
    $deaths = ($game['deaths'] ?? 0);
    $savedGame['deaths'] = $deaths;
    $savedGame['phase']  = 'lobby';
    $savedGame['current_movie'] = null;
    $savedGame['movie_start_message_id'] = null;
    writeJson($gameFile, $savedGame);
    // Trim chat to pre-movie state
    $chat = readJson($chatFile);
    $movieStartId = $game['movie_start_message_id'] ?? null;
    if ($movieStartId && $chat) {
        $chat['messages'] = array_values(array_filter(
            $chat['messages'],
            fn($m) => ($m['id'] ?? 0) < $movieStartId
        ));
        $chat['messages'][] = [
            'id'        => nextMsgId($chat),
            'sender'    => 'system',
            'content'   => 'Save restored from ' . $file . '. Welcome back to God\'s Space.',
            'timestamp' => date('c'),
        ];
        $chat['status'] = 'waiting_for_player';
        writeJson($chatFile, $chat);
    }
    echo json_encode(['ok' => true, 'restored_from' => $file]);
    exit;
}

// ── List lobby saves ──────────────────────────────────────
if ($action === 'list-saves') {
    $saves = [];
    $savesDir = $base . '/saves/';
    if (is_dir($savesDir)) {
        foreach (glob($savesDir . 'lobby-*.json') as $f) {
            $data = readJson($f);
            $saves[] = [
                'file'        => basename($f),
                'movie_num'   => $data['movie_number'] ?? 0,
                'points'      => $data['points'] ?? 0,
                'char_name'   => $data['character']['name'] ?? 'Unknown',
                'phase'       => $data['phase'] ?? 'unknown',
                'mtime'       => filemtime($f),
            ];
        }
        usort($saves, fn($a,$b) => $b['mtime'] - $a['mtime']);
    }
    echo json_encode(['saves' => $saves]);
    exit;
}

// ── Update game state field (for UI direct updates) ────────
// ── Save a Freesound ID for a sound key ──────────────────
if ($action === 'save-sound-id' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $soundsFile = $base . '/system/sounds.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $key  = trim($input['key']  ?? '');
    $fsId = $input['id']; // may be null to clear

    if (!$key) { http_response_code(400); echo json_encode(['error' => 'No key']); exit; }

    $sounds = readJson($soundsFile);
    if (!$sounds) {
        http_response_code(500); echo json_encode(['error' => 'Cannot read sounds file']); exit;
    }
    // Auto-create entry if key doesn't exist
    if (!isset($sounds['sounds'][$key])) {
        $sounds['sounds'][$key] = [
            'label' => $key,
            'description' => '',
            'freesound_id' => null,
            'audio_url' => null,
        ];
    }
    // Ensure loop defaults to true
    if (!isset($sounds['sounds'][$key]['loop'])) {
        $sounds['sounds'][$key]['loop'] = true;
    }

    $sounds['sounds'][$key]['freesound_id'] = $fsId ? (int)$fsId : null;
    // Save loop toggle if provided
    if (isset($input['loop'])) {
        $sounds['sounds'][$key]['loop'] = (bool)$input['loop'];
    }
    // Also save direct audio URL if provided
    $audioUrl = trim($input['audio_url'] ?? '');
    $sounds['sounds'][$key]['audio_url'] = $audioUrl ?: null;
    writeJson($soundsFile, $sounds);
    echo json_encode(['ok' => true, 'key' => $key, 'id' => $fsId ? (int)$fsId : null, 'audio_url' => $audioUrl ?: null]);
    exit;
}

// ── Save YouTube ID for a music track ────────────────────
if ($action === 'save-music-id' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $musicFile = $base . '/system/music.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $index = (int)($input['index'] ?? -1);
    $ytId  = trim($input['youtube_id'] ?? '');

    $music = readJson($musicFile);
    if (!$music || !isset($music['tracks'][$index])) {
        http_response_code(404); echo json_encode(['error' => 'Track not found']); exit;
    }

    $music['tracks'][$index]['youtube_id'] = $ytId ?: null;
    writeJson($musicFile, $music);
    echo json_encode(['ok' => true, 'index' => $index, 'youtube_id' => $ytId ?: null]);
    exit;
}

// ── Fetch YouTube video info (server-side, avoids CORS) ───
if ($action === 'fetch-yt-info') {
    $url = urldecode($_GET['url'] ?? '');
    if (!$url || !preg_match('/youtube\.com|youtu\.be/', $url)) {
        http_response_code(400); echo json_encode(['error' => 'Invalid YouTube URL']); exit;
    }
    $oembedUrl = 'https://www.youtube.com/oembed?url=' . urlencode($url) . '&format=json';
    $ctx = stream_context_create(['http' => ['timeout' => 8, 'user_agent' => 'Mozilla/5.0 (compatible)']]);
    $res = @file_get_contents($oembedUrl, false, $ctx);
    if (!$res) { http_response_code(502); echo json_encode(['error' => 'Could not reach YouTube. Check the URL is public.']); exit; }
    $data = json_decode($res, true);
    preg_match('/(?:v=|youtu\.be\/|embed\/)([A-Za-z0-9_\-]{11})/', $url, $m);
    echo json_encode([
        'title'    => $data['title'] ?? '',
        'author'   => $data['author_name'] ?? '',
        'video_id' => $m[1] ?? null,
    ]);
    exit;
}

// ── Replace MUSIC-SEARCH tag with MUSIC tag in chat ──────
if ($action === 'replace-music-search' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $chatFile = $base . '/data/chat.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $searchQuery = trim($input['search_query'] ?? '');
    $trackId = trim($input['track_id'] ?? '');
    if (!$searchQuery || !$trackId) {
        http_response_code(400); echo json_encode(['error' => 'Missing search_query or track_id']); exit;
    }
    $chat = readJson($chatFile);
    if (!$chat) { http_response_code(500); echo json_encode(['error' => 'Cannot read chat.json']); exit; }
    $changed = false;
    foreach ($chat['messages'] as &$msg) {
        if ($msg['sender'] === 'gm' && strpos($msg['content'], '[MUSIC-SEARCH:' . $searchQuery . ']') !== false) {
            $msg['content'] = str_replace('[MUSIC-SEARCH:' . $searchQuery . ']', '[MUSIC:' . $trackId . ']', $msg['content']);
            $changed = true;
        }
    }
    if ($changed) writeJson($chatFile, $chat);
    echo json_encode(['ok' => true, 'changed' => $changed]);
    exit;
}

// ── Add a single music track ──────────────────────────────
if ($action === 'add-music' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $musicFile = $base . '/system/music.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $music = readJson($musicFile);
    if (!$music) { http_response_code(500); echo json_encode(['error' => 'Cannot read music.json']); exit; }

    $ytId = trim($input['youtube_id'] ?? '');
    $title = trim($input['title'] ?? 'Unknown');
    $artist = trim($input['artist'] ?? 'Unknown');

    // Prevent duplicates by youtube_id
    if ($ytId) {
        foreach ($music['tracks'] as $t) {
            if (($t['youtube_id'] ?? '') === $ytId) {
                echo json_encode(['ok' => false, 'error' => 'Track already in library', 'track' => $t]);
                exit;
            }
        }
    }

    $track = [
        'id'           => 'custom-' . ($ytId ?: uniqid()),
        'title'        => $title,
        'artist'       => $artist,
        'category'     => $input['category'] ?? 'Custom',
        'youtube_id'   => $ytId ?: null,
        'search_query' => $title . ' ' . $artist,
        'mood'         => $input['mood'] ?? '',
        'bpm'          => '',
        'custom'       => true,
    ];
    $music['tracks'][] = $track;
    // Ensure 'Custom' is in categories
    if (!in_array('Custom', $music['categories'] ?? [])) {
        $music['categories'][] = 'Custom';
    }
    writeJson($musicFile, $music);
    echo json_encode(['ok' => true, 'track' => $track]);
    exit;
}

// ── Remove a music track ──────────────────────────────────
if ($action === 'remove-music' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $musicFile = $base . '/system/music.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $trackId = $input['id'] ?? '';
    if (!$trackId) { http_response_code(400); echo json_encode(['error' => 'No id']); exit; }
    $music = readJson($musicFile);
    if (!$music) { http_response_code(500); echo json_encode(['error' => 'Cannot read music.json']); exit; }
    $before = count($music['tracks'] ?? []);
    $music['tracks'] = array_values(array_filter($music['tracks'] ?? [], fn($t) => ($t['id'] ?? '') !== $trackId));
    writeJson($musicFile, $music);
    echo json_encode(['ok' => true, 'removed' => $before - count($music['tracks'])]);
    exit;
}

// ── Add all videos from a YouTube playlist ────────────────
if ($action === 'add-playlist' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $musicFile = $base . '/system/music.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $rawUrl = trim($input['url'] ?? '');
    $category = $input['category'] ?? 'Custom';

    preg_match('/[?&]list=([A-Za-z0-9_\-]+)/', $rawUrl, $pm);
    $playlistId = $pm[1] ?? null;
    if (!$playlistId) { http_response_code(400); echo json_encode(['error' => 'Could not find playlist ID in URL. Make sure the URL contains ?list=...']); exit; }

    $rssUrl = 'https://www.youtube.com/feeds/videos.xml?playlist_id=' . urlencode($playlistId);
    $ctx = stream_context_create(['http' => ['timeout' => 12, 'user_agent' => 'Mozilla/5.0 (compatible)']]);
    $rss = @file_get_contents($rssUrl, false, $ctx);
    if (!$rss) { http_response_code(502); echo json_encode(['error' => 'Could not fetch playlist. Make sure it is public and the URL is correct.']); exit; }

    libxml_use_internal_errors(true);
    $xml = simplexml_load_string($rss);
    if (!$xml) { http_response_code(502); echo json_encode(['error' => 'Could not parse playlist XML']); exit; }

    $music = readJson($musicFile);
    if (!$music) { http_response_code(500); echo json_encode(['error' => 'Cannot read music.json']); exit; }

    // Build existing ID set to avoid duplicates
    $existingIds = array_column($music['tracks'] ?? [], 'youtube_id');

    $added = []; $skipped = 0;
    foreach ($xml->entry as $entry) {
        $ns = $entry->getNamespaces(true);
        $ytNs = array_filter(array_keys($ns), fn($k) => $k === 'yt');
        $ytKey = reset($ytNs) ?: 'yt';
        $ytEl = $entry->children($ns[$ytKey] ?? 'http://www.youtube.com/xml/schemas/2015');
        $videoId = (string)($ytEl->videoId ?? '');
        $title   = (string)($entry->title ?? 'Unknown');
        $author  = (string)($entry->author->name ?? 'Unknown');

        if (!$videoId) continue;
        if (in_array($videoId, $existingIds)) { $skipped++; continue; }

        $track = [
            'id'           => 'custom-' . $videoId,
            'title'        => $title,
            'artist'       => $author,
            'category'     => $category,
            'youtube_id'   => $videoId,
            'search_query' => $title . ' ' . $author,
            'mood'         => '',
            'bpm'          => '',
            'custom'       => true,
        ];
        $music['tracks'][] = $track;
        $existingIds[] = $videoId;
        $added[] = $title;
    }

    if (!in_array('Custom', $music['categories'] ?? [])) {
        $music['categories'][] = 'Custom';
    }
    writeJson($musicFile, $music);
    echo json_encode(['ok' => true, 'added' => count($added), 'skipped' => $skipped, 'titles' => $added]);
    exit;
}

// ── Start the watcher engine (detached) ───────────────────
if ($action === 'start-watcher') {
    // Already running? (last_tick within 10s)
    $game = readJson($base . '/data/game.json');
    $lt = $game['watcher']['last_tick'] ?? null;
    if ($lt && (time() - strtotime($lt)) < 10) {
        echo json_encode(['ok' => true, 'already_running' => true]);
        exit;
    }
    $bat = $base . '\\watcher\\run-watcher.bat';
    if (!file_exists($bat)) {
        http_response_code(500);
        echo json_encode(['error' => 'run-watcher.bat not found at ' . $bat]);
        exit;
    }
    // Fire-and-forget detached launch (Windows). The bat opens its own window.
    $cmd = 'start /MIN "TI-Watcher" "' . $bat . '"';
    pclose(popen($cmd, 'r'));
    echo json_encode(['ok' => true, 'started' => true]);
    exit;
}

// ── Watcher status ────────────────────────────────────────
if ($action === 'watcher-status') {
    $game = readJson($base . '/data/game.json');
    $lt = $game['watcher']['last_tick'] ?? null;
    $running = $lt ? ((time() - strtotime($lt)) < 10) : false;
    echo json_encode(['running' => $running, 'last_tick' => $lt]);
    exit;
}

// ── Get event log (raw text) ──────────────────────────────
// ── Save watcher config (ai_tool, ai_model) ────────────────
if ($action === 'save-watcher-config' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $configFile = $base . '/watcher/config.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $config = readJson($configFile);
    if (!$config) {
        http_response_code(500); echo json_encode(['error' => 'Cannot read config']); exit;
    }
    if (isset($input['ai_tool'])) {
        $config['settings']['ai_tool'] = in_array($input['ai_tool'], ['claude', 'opencode']) ? $input['ai_tool'] : 'claude';
    }
    if (isset($input['ai_model'])) {
        $config['settings']['ai_model'] = trim($input['ai_model']) ?? '';
    }
    writeJson($configFile, $config);
    echo json_encode(['ok' => true, 'ai_tool' => $config['settings']['ai_tool'], 'ai_model' => $config['settings']['ai_model']]);
    exit;
}

// ── Stop the watcher engine ────────────────────────────────
if ($action === 'stop-watcher') {
    exec('taskkill /f /fi "WINDOWTITLE eq TI-Watcher" 2>nul', $output, $rc);
    echo json_encode(['ok' => true, 'killed' => ($rc === 0)]);
    exit;
}

// ── Get watcher config ─────────────────────────────────────
if ($action === 'get-watcher-config') {
    $configFile = $base . '/watcher/config.json';
    $config = readJson($configFile);
    if (!$config) {
        http_response_code(500); echo json_encode(['error' => 'Cannot read config']); exit;
    }
    echo json_encode([
        'ai_tool' => $config['settings']['ai_tool'] ?? 'claude',
        'ai_model' => $config['settings']['ai_model'] ?? '',
    ]);
    exit;
}

// (freesound endpoint removed — uses direct iframe embed instead)

http_response_code(400);
echo json_encode(['error' => 'Unknown action: ' . htmlspecialchars($action)]);
