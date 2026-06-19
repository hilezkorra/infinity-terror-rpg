#!/usr/bin/env python3
"""
Batch 2 & 3: Expand nationality name pools + add occupation probability boosts.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEAM_GEN = ROOT / 'system' / 'team-gen.json'

with open(TEAM_GEN, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Build index by country name
nats = {n['country']: n for n in data['nationalities']}

# ════════════════════════════════════════════════════════════════
# EXPANDED NAME POOLS
# ════════════════════════════════════════════════════════════════

NAMES = {
    'German': {
        'male': ['Klaus','Stefan','Markus','Thomas','Michael','Andreas','Wolfgang','Jürgen','Hans','Dieter','Uwe','Frank','Ralf','Bernd','Heinz','Günter','Matthias','Sebastian','Florian','Tobias','Felix','Lukas','Maximilian','Simon','Julian','Fabian','Niklas','Jonas','Leon','Erik'],
        'female': ['Anna','Sophie','Laura','Lena','Julia','Sarah','Katharina','Hanna','Maria','Sabine','Petra','Monika','Ursula','Renate','Brigitte','Angelika','Heike','Sandra','Nicole','Stefanie','Christina','Jennifer','Vanessa','Nadine','Sabrina','Isabella','Mia','Lina','Emma','Lea'],
        'surnames': ['Schmidt','Müller','Schneider','Fischer','Weber','Wagner','Becker','Hoffmann','Schäfer','Koch','Bauer','Richter','Klein','Wolf','Schröder','Neumann','Schwarz','Zimmermann','Braun','Krüger','Hofmann','Hartmann','Lange','Schmitt','Werner','Krause','Meier','Lehmann','Schulze','Maier']
    },
    'French': {
        'male': ['Pierre','Antoine','Julien','Nicolas','Alexandre','Mathieu','Jérôme','Christophe','Sébastien','Romain','Quentin','Florian','Guillaume','Olivier','Thibault','Loïc','Cédric','Ludovic','Maxime','Kevin','Raphaël','Adrien','Clément','Hugo','Lucas','Théo','Nathan','Louis','Gabriel','Jules'],
        'female': ['Camille','Marie','Léa','Manon','Chloé','Clara','Sarah','Laura','Justine','Julie','Sophie','Nathalie','Céline','Isabelle','Valérie','Sandrine','Stéphanie','Audrey','Émilie','Jessica','Marion','Océane','Morgane','Pauline','Lucie','Amandine','Elodie','Mélanie','Anaïs','Aurélie'],
        'surnames': ['Martin','Bernard','Dubois','Thomas','Robert','Richard','Petit','Durand','Leroy','Moreau','Simon','Laurent','Lefebvre','Michel','Garcia','David','Bertrand','Roux','Vincent','Fournier','Morel','Girard','André','Lefèvre','Mercier','Dupont','Lambert','Bonnet','François','Martinez']
    },
    'Italian': {
        'male': ['Marco','Luca','Alessandro','Francesco','Matteo','Giuseppe','Antonio','Giovanni','Lorenzo','Andrea','Paolo','Roberto','Claudio','Fabio','Massimo','Sergio','Alberto','Federico','Stefano','Riccardo','Simone','Emanuele','Davide','Michele','Leonardo','Tommaso','Edoardo','Alessio','Nicolò','Diego'],
        'female': ['Giulia','Sara','Martina','Francesca','Chiara','Elena','Valentina','Anna','Maria','Laura','Paola','Caterina','Simona','Alessandra','Barbara','Monica','Silvia','Rosa','Luisa','Daniela','Beatrice','Giorgia','Federica','Veronica','Serena','Elisa','Marta','Eleonora','Viola','Aurora'],
        'surnames': ['Rossi','Russo','Ferrari','Esposito','Bianchi','Romano','Colombo','Ricci','Marino','Greco','Bruno','Gallo','Conti','De Luca','Mancini','Costa','Giordano','Rinaldi','Moretti','Barbieri','Fontana','Santoro','Mariani','Pellegrino','Vitali','Sartori','Guerra','Carbone','Palmieri','Serra']
    },
    'Spanish': {
        'male': ['Alejandro','Carlos','Miguel','José','Antonio','Javier','Francisco','David','Manuel','Pablo','Jorge','Luis','Fernando','Sergio','Alberto','Daniel','Adrián','Juan','Álvaro','Diego','Marcos','Jesús','Víctor','Raúl','Iván','Hugo','Álex','Mario','Rubén','Óscar'],
        'female': ['Carmen','María','Ana','Laura','Patricia','Teresa','Rosa','Sara','Cristina','Dolores','Marta','Isabel','Elena','Beatriz','Sofía','Paula','Raquel','Ángela','Nerea','Claudia','Lucía','Alicia','Nuria','Silvia','Esther','Julia','Pilar','Eva','Lorena','Ruth'],
        'surnames': ['García','Rodríguez','Martínez','López','González','Fernández','Sánchez','Pérez','Martín','Jiménez','Ruiz','Hernández','Díaz','Moreno','Álvarez','Muñoz','Romero','Navarro','Torres','Domínguez','Gil','Vázquez','Serrano','Ramos','Castro','Suárez','Ortega','Rubio','Molina','Delgado']
    },
    'Polish': {
        'male': ['Piotr','Marek','Krzysztof','Tomasz','Andrzej','Paweł','Jan','Michał','Jakub','Mateusz','Adam','Łukasz','Bartosz','Dawid','Marcin','Grzegorz','Rafał','Jacek','Wojciech','Zbigniew','Kamil','Maciej','Artur','Damian','Szymon','Patryk','Filip','Wiktor','Sebastian','Igor'],
        'female': ['Anna','Katarzyna','Magdalena','Agnieszka','Joanna','Małgorzata','Ewa','Monika','Marta','Barbara','Elżbieta','Zofia','Aleksandra','Natalia','Paulina','Justyna','Kinga','Klaudia','Sylwia','Dorota','Alicja','Renata','Beata','Patrycja','Oliwia','Emilia','Weronika','Izabela','Aneta','Marzena'],
        'surnames': ['Nowak','Kowalski','Wiśniewski','Dąbrowski','Lewandowski','Wójcik','Kamiński','Kowalczyk','Zieliński','Szymański','Woźniak','Kozłowski','Jankowski','Mazur','Wojciechowski','Kwiatkowski','Krawczyk','Piotrowicz','Grabowski','Nowakowski','Pawlak','Michalski','Wróbel','Wieczorek','Baranowski','Jabłoński','Sadowski','Jakubowski','Szczepański','Ostrowski']
    },
    'Russian': {
        'male': ['Alexei','Dmitri','Nikolai','Vladimir','Ivan','Mikhail','Sergei','Andrei','Yuri','Boris','Pavel','Viktor','Anatoly','Oleg','Grigory','Konstantin','Vasily','Roman','Stepan','Yaroslav','Maxim','Artyom','Egor','Denis','Ilya','Timofey','Leonid','Fyodor','Gleb','Petr'],
        'female': ['Natasha','Olga','Tatiana','Elena','Anastasia','Maria','Irina','Svetlana','Yekaterina','Galina','Anna','Nina','Ludmila','Valentina','Vera','Marina','Daria','Polina','Yulia','Sofia','Alina','Ksenia','Viktoria','Elizaveta','Alexandra','Nadezhda','Tamara','Larisa','Margarita','Oksana'],
        'surnames': ['Ivanov','Petrov','Sidorov','Kuznetsov','Smirnov','Popov','Volkov','Sokolov','Lebedev','Kozlov','Novikov','Morozov','Fyodorov','Mikhailov','Andreev','Nikolaev','Alexeev','Zaitsev','Solovyov','Vasiliev','Romanov','Grigoriev','Pavlov','Orlov','Zakharov','Frolov','Dmitriev','Belyaev','Matveev','Titov']
    },
    'British': {
        'male': ['James','William','Jack','George','Oliver','Harry','Charlie','Henry','Thomas','Edward','Arthur','Albert','Alfred','Robert','David','Richard','Charles','John','Michael','Peter','Simon','Andrew','Daniel','Christopher','Matthew','Stephen','Paul','Mark','Anthony','Philip'],
        'female': ['Charlotte','Emily','Alice','Olivia','Amelia','Sophie','Florence','Isabella','Jessica','Eleanor','Elizabeth','Victoria','Rose','Grace','Lily','Emma','Mary','Sarah','Margaret','Helen','Joanna','Catherine','Claire','Rebecca','Rachel','Laura','Hannah','Amy','Lucy','Julia'],
        'surnames': ['Smith','Jones','Williams','Taylor','Brown','Davies','Wilson','Evans','Thomas','Roberts','Johnson','Walker','Wright','Thompson','White','Hughes','Edwards','Green','Hall','Wood','Harris','Marin','Jackson','Clarke','Turner','Hill','Moore','Clark','King','Cooper']
    },
    'Irish': {
        'male': ['Ciarán','Eoin','Seán','Patrick','Liam','Oisin','Conor','Fionn','Niall','Declan','Rory','Darragh','Cillian','Finn','Cathal','Aidan','Cormac','Kieran','Brian','Donal','Fergus','Colm','Ronan','Padraig','Tadhg','Eamon','Shane','Kevin','Brendan','Dermot'],
        'female': ['Aoife','Siobhán','Fionnuala','Niamh','Saoirse','Ciara','Roisin','Maeve','Grainne','Aisling','Orla','Eimear','Deirdre','Caitlin','Sinead','Mairead','Bridget','Clodagh','Aine','Cara','Eilis','Muireann','Riona','Sile','Treasa','Una','Sorcha','Laoise','Meadhbh','Ailbhe'],
        'surnames': ['Murphy','O\'Brien','Kelly','O\'Sullivan','Walsh','Ryan','O\'Connor','O\'Neill','O\'Reilly','Doyle','McCarthy','Farrell','Dunne','Burke','Hartnett','Flynn','Donnelly','Brennan','Moore','Fitzgerald','Nolan','Connolly','Healy','Casey','Byrne','Cunningham','O\'Donnell','Cullen','Higgins','Lynch']
    },
    'Swedish': {
        'male': ['Erik','Lars','Johan','Anders','Karl','Per','Mikael','Magnus','Sven','Björn','Nils','Ulf','Jan','Olof','Gustav','Henrik','Fredrik','Tobias','Jonas','Oskar','Viktor','Emil','Hugo','Linus','Simon','Alexander','William','Oscar','Elias','Noah'],
        'female': ['Astrid','Ingrid','Maja','Alma','Ebba','Elsa','Signe','Ulla','Kerstin','Birgitta','Gunilla','Eva','Anna','Maria','Lena','Sofia','Emma','Linnea','Alice','Wilma','Klara','Tyra','Freja','Stina','Tove','Saga','Lovisa','Nora','Selma','Elvira'],
        'surnames': ['Johansson','Andersson','Karlsson','Nilsson','Eriksson','Larsson','Olsson','Persson','Svensson','Gustafsson','Pettersson','Jonsson','Hansson','Bengtsson','Jönsson','Lindberg','Jakobsson','Bergström','Lindström','Lundqvist','Mattsson','Berg','Sandberg','Lindgren','Forsberg','Sjöberg','Wallin','Engström','Holm','Nyström']
    },
    'Norwegian': {
        'male': ['Magnus','Tor','Bjørn','Olav','Harald','Erik','Leif','Rune','Kjell','Arne','Per','Jan','Svein','Geir','Morten','Lars','Anders','Henrik','Kristian','Sander','Markus','Emil','Noah','Oliver','Filip','Jonas','Simen','Håkon','Mats','Jørgen'],
        'female': ['Sigrid','Ingrid','Solveig','Astrid','Liv','Greta','Kari','Hilde','Ragnhild','Turid','Berit','Anne','Marte','Ida','Emma','Nora','Sofie','Maja','Linnea','Thea','Sara','Hanna','Tiril','Oda','Julie','Inger','Helene','Celine','Vilde','Ine'],
        'surnames': ['Hansen','Johansen','Olsen','Larsen','Andersen','Pedersen','Nilsen','Kristiansen','Jensen','Karlsen','Johnsen','Eriksen','Berg','Svendsen','Haugen','Hagen','Johannessen','Moan','Eide','Gundersen','Myhre','Solberg','Moen','Strand','Bakken','Kristoffersen','Berge','Aasen','Dahl','Fredriksen']
    },
    'Dutch': {
        'male': ['Jan','Pieter','Bas','Henk','Dirk','Willem','Kees','Joost','Thijs','Sander','Bram','Jasper','Daan','Tim','Lars','Max','Ruben','Thomas','Jesse','Milan','Levi','Luuk','Sem','Joris','Gijs','Wout','Hugo','Finn','Niels','Michiel'],
        'female': ['Femke','Anouk','Lotte','Sanne','Lieke','Lisa','Eva','Anna','Emma','Iris','Sara','Nina','Laura','Marjolein','Birgit','Wilma','Joke','Tineke','Mieke','Bianca','Sofie','Noa','Yara','Luna','Roos','Vera','Feline','Benthe','Jolien','Maud'],
        'surnames': ['de Jong','Jansen','de Vries','van den Berg','van Dijk','Bakker','Visser','Smit','Meijer','de Boer','Mulder','de Groot','Bos','Vos','Peters','Hendriks','van Leeuwen','Dekker','Brouwer','de Wit','Dijkstra','de Bruin','Rutten','van der Heijden','Blom','Damen','van der Meer','Willems','van Loon','Kuipers']
    },
    'Portuguese': {
        'male': ['João','Pedro','Tiago','Manuel','José','António','Francisco','Carlos','Rui','Luís','Ricardo','Miguel','Nuno','André','Paulo','Hugo','Bruno','Daniel','Rafael','Martim','Santiago','Diogo','Tomás','Vasco','David','Gonçalo','Filipe','Rui','Jorge','Leandro'],
        'female': ['Sofia','Ana','Mariana','Maria','Carla','Rita','Inês','Joana','Catarina','Ana','Cláudia','Sara','Marta','Beatriz','Leonor','Carolina','Margarida','Daniela','Filipa','Patrícia','Diana','Ânia','Lara','Matilde','Eva','Francisca','Luana','Iara','Raquel','Telma'],
        'surnames': ['Silva','Santos','Ferreira','Pereira','Oliveira','Costa','Rodrigues','Martins','Jesus','Sousa','Fernandes','Gonçalves','Gomes','Lopes','Marques','Almeida','Ribeiro','Pinto','Carvalho','Teixeira','Moreira','Correia','Mendes','Neves','Nunes','Vieira','Cardoso','Soares','Cavaco','Vale']
    },
    'Ukrainian': {
        'male': ['Oleksandr','Dmytro','Bohdan','Andrii','Mykola','Volodymyr','Serhii','Petro','Ivan','Pavlo','Vasyl','Yurii','Oleh','Mykhailo','Taras','Roman','Maksym','Artem','Denys','Vladyslav','Yevhen','Viktor','Borys','Hryhorii','Illia','Marko','Kyrylo','Nazar','Stanislav','Danylo'],
        'female': ['Olena','Tetiana','Iryna','Nataliia','Mariia','Anna','Halyna','Kateryna','Liudmyla','Svitlana','Yuliia','Anastasiia','Viktoriia','Lesia','Oksana','Nadiia','Larysa','Tamara','Vira','Zoriana','Solomiia','Ivanna','Daryna','Sofiia','Polina','Karina','Marta','Khrystyna','Alina','Milana'],
        'surnames': ['Melnyk','Shevchenko','Boyko','Kovalenko','Bondarenko','Tkachenko','Kravchenko','Kovalchuk','Oliynyk','Shevchuk','Polishchuk','Lysenko','Rudenko','Savchenko','Petrenko','Klymenko','Pavlenko','Vasylenko','Yakovenko','Tarasenko','Ponomarenko','Chernenko','Marchenko','Koval','Hrytsenko','Danilova','Nesterenko','Hrytsenko','Myronenko','Zhdanov']
    },
    'Japanese': {
        'male': ['Kenji','Hiroshi','Takeshi','Yuki','Satoshi','Taro','Ryo','Kaito','Haruki','Sota','Yuto','Sho','Daiki','Naoki','Takashi','Koji','Shinji','Yoshio','Kazuki','Tatsuya','Ryota','Shota','Kenta','Jun','Kazuya','Riku','Yamato','Hayato','Subaru','Ren'],
        'female': ['Yuki','Sakura','Hana','Aoi','Rin','Miyu','Yui','Nao','Mei','Sara','Akari','Hinata','Mizuki','Riko','Aya','Miki','Chihiro','Yoko','Rei','Kaori','Misaki','Saki','Aimi','Mana','Ai','Eri','Asuka','Nana','Marina','Emi'],
        'surnames': ['Sato','Suzuki','Takahashi','Tanaka','Watanabe','Ito','Yamamoto','Nakamura','Ogawa','Kato','Yoshida','Yamada','Sasaki','Yamaguchi','Matsumoto','Inoue','Kimura','Hayashi','Shimizu','Abe','Mori','Ikeda','Hashimoto','Yamashita','Ishikawa','Nakajima','Maeda','Fujita','Ogata','Goto']
    },
    'Korean': {
        'male': ['Joon','Hyun','Sung','Min-ho','Ji-hoon','Seung-min','Young-jun','Jae-won','Hyun-woo','Dong-hyun','Sang-hyun','Yong-woo','Ki-hoon','Jin-woo','Chang-min','Yoon-seok','Tae-yun','Kang-min','Seok-jin','Hee-chul','Kyung-ho','Woo-jin','Jun-seo','Hyuk','Myung-ho','Jeong-hoon','In-sik','Byung-ho','Dae-hyun','Han-gil'],
        'female': ['Ji-yeon','Soo-ah','Hye-jin','Min-ji','Eun-jung','Yeon-woo','Seo-yeon','Jin-ah','Hee-jin','Eun-ji','So-young','Mi-young','Kyung-ae','Sung-hee','Yoon-ji','Ye-jin','Ji-soo','Na-young','Hwa-young','Seung-ah','Bo-ram','Jung-im','Hyun-jung','Sun-young','Soo-yeon','Ae-jung','In-sook','Joo-hee','Mi-na','Ha-na'],
        'surnames': ['Kim','Lee','Park','Choi','Jung','Kang','Cho','Yoon','Oh','Kim','Ryu','Jang','Shin','Kwon','Hwang','Ahn','Song','Jeon','Yoo','Hong','Moon','Yang','Ko','Seo','Bae','Rim','Ha','Paik','Chun','Han']
    },
    'Brazilian': {
        'male': ['Lucas','Gustavo','Rafael','Mateus','Gabriel','Felipe','Pedro','João','Marcos','Paulo','Carlos','José','Antonio','Tiago','Bruno','Vitor','Diego','Eduardo','Rodrigo','Igor','Caio','Henrique','Leonardo','Vinicius','Douglas','Alexandre','Thiago','André','Guilherme','Daniel'],
        'female': ['Júlia','Ana','Larissa','Beatriz','Camila','Fernanda','Mariana','Amanda','Roberta','Carla','Patrícia','Simone','Renata','Vanessa','Juliana','Carolina','Paula','Letícia','Priscila','Isabela','Aline','Bianca','Luciana','Daniela','Gabriela','Eduarda','Lorena','Rafaela','Vitória','Alice'],
        'surnames': ['Silva','Santos','Oliveira','Souza','Rodrigues','Lima','Almeida','Costa','Pereira','Carvalho','Gomes','Martins','Barbosa','Ribeiro','Araújo','Dias','Moreira','Nascimento','Correia','Mendes','Cardoso','Barros','Teixeira','Cavalcanti','Fernandes','Rocha','Vieira','Campos','Melo','Azevedo']
    },
    'Czech': {
        'male': ['Jakub','Pavel','Tomáš','Jan','Petr','Josef','Milan','Václav','Jiří','Karel','Zdeněk','Vladimír','Ondřej','David','Martin','Lukáš','Filip','Adam','Matyáš','Vojtěch','Dominik','Štěpán','Michal','Marek','Daniel','Ota','František','René','Vít','Ivan'],
        'female': ['Tereza','Lucie','Markéta','Eva','Anna','Marie','Jana','Petra','Kateřina','Pavla','Veronika','Helena','Lenka','Zuzana','Ilona','Věra','Dana','Michaela','Karolína','Nikola','Kristýna','Adéla','Barbora','Eliška','Alena','Hana','Monika','Iveta','Simona','Renata'],
        'surnames': ['Novák','Svoboda','Novotný','Dvořák','Černý','Procházka','Kučera','Veselý','Horák','Němec','Marek','Pospíšil','Krejčí','Pokorný','Hájek','Jelínek','Král','Růžička','Beneš','Fiala','Sedláček','Kolář','Mašek','Šimek','Kubát','Šmíd','Urban','Pavlíček','Müller','Váňa']
    }
}

# Apply name expansions
for country, pools in NAMES.items():
    if country in nats:
        n = nats[country]
        # Extend male names
        existing_m = [x.lower() for x in n.get('male', [])]
        for name in pools['male']:
            if name.lower() not in existing_m:
                n['male'].append(name)
                existing_m.append(name.lower())
        # Extend female names
        existing_f = [x.lower() for x in n.get('female', [])]
        for name in pools['female']:
            if name.lower() not in existing_f:
                n['female'].append(name)
                existing_f.append(name.lower())
        # Extend surnames
        existing_s = [x.lower() for x in n.get('surnames', [])]
        for name in pools['surnames']:
            if name.lower() not in existing_s:
                n['surnames'].append(name)
                existing_s.append(name.lower())
        print(f'{country}: male={len(n["male"])} (+{len(pools["male"])}), female={len(n["female"])} (+{len(pools["female"])}), surnames={len(n["surnames"])} (+{len(pools["surnames"])})')
    else:
        print(f'WARNING: {country} not found in nationalities!')

# ════════════════════════════════════════════════════════════════
# OCCUPATION BOOSTS
# ════════════════════════════════════════════════════════════════
# occupation_boosts: list of occupation IDs or partial label matches
# format: { "occupation": "label_contains", "multiplier": 3 }

BOOSTS = {
    'German': [
        {'occupation': 'Engineer', 'multiplier': 3},
        {'occupation': 'Brewer', 'multiplier': 4},
        {'occupation': 'Soldier', 'multiplier': 2},
        {'occupation': 'Scientist', 'multiplier': 2},
        {'occupation': 'Philosopher', 'multiplier': 3},
        {'occupation': 'Mechanic', 'multiplier': 2},
        {'occupation': 'Chemist', 'multiplier': 2},
    ],
    'French': [
        {'occupation': 'Chef', 'multiplier': 3},
        {'occupation': 'Fashion', 'multiplier': 3},
        {'occupation': 'Artist', 'multiplier': 2},
        {'occupation': 'Sommelier', 'multiplier': 4},
        {'occupation': 'Perfume', 'multiplier': 3},
        {'occupation': 'Baker', 'multiplier': 2},
        {'occupation': 'Mime', 'multiplier': 4},
    ],
    'Italian': [
        {'occupation': 'Mafia', 'multiplier': 3},
        {'occupation': 'Chef', 'multiplier': 3},
        {'occupation': 'Fashion', 'multiplier': 2},
        {'occupation': 'Pizza', 'multiplier': 4},
        {'occupation': 'Don', 'multiplier': 4},
        {'occupation': 'Barista', 'multiplier': 2},
        {'occupation': 'Designer', 'multiplier': 2},
    ],
    'Spanish': [
        {'occupation': 'Dancer', 'multiplier': 2},
        {'occupation': 'Chef', 'multiplier': 2},
        {'occupation': 'Missionary', 'multiplier': 3},
        {'occupation': 'Conquistador', 'multiplier': 4},
        {'occupation': 'Mercenary', 'multiplier': 2},
        {'occupation': 'Pilot', 'multiplier': 2},
    ],
    'Polish': [
        {'occupation': 'Plumber', 'multiplier': 3},
        {'occupation': 'Construction', 'multiplier': 2},
        {'occupation': 'Mechanic', 'multiplier': 2},
        {'occupation': 'Priest', 'multiplier': 3},
        {'occupation': 'Miner', 'multiplier': 3},
        {'occupation': 'Electrician', 'multiplier': 2},
    ],
    'Russian': [
        {'occupation': 'Spy', 'multiplier': 3},
        {'occupation': 'Soldier', 'multiplier': 2},
        {'occupation': 'Scientist', 'multiplier': 2},
        {'occupation': 'Ballet', 'multiplier': 4},
        {'occupation': 'Chess', 'multiplier': 3},
        {'occupation': 'Pilot', 'multiplier': 2},
        {'occupation': 'Intelligence', 'multiplier': 3},
        {'occupation': 'Mercenary', 'multiplier': 2},
    ],
    'British': [
        {'occupation': 'MI6', 'multiplier': 5},
        {'occupation': 'Butler', 'multiplier': 4},
        {'occupation': 'Banker', 'multiplier': 2},
        {'occupation': 'Journalist', 'multiplier': 2},
        {'occupation': 'Royal', 'multiplier': 3},
        {'occupation': 'Guard', 'multiplier': 2},
        {'occupation': 'Detective', 'multiplier': 2},
    ],
    'Irish': [
        {'occupation': 'Priest', 'multiplier': 3},
        {'occupation': 'Pub', 'multiplier': 4},
        {'occupation': 'Boxer', 'multiplier': 2},
        {'occupation': 'Poet', 'multiplier': 3},
        {'occupation': 'Bartender', 'multiplier': 2},
        {'occupation': 'Construction', 'multiplier': 2},
    ],
    'Swedish': [
        {'occupation': 'Engineer', 'multiplier': 2},
        {'occupation': 'Soldier', 'multiplier': 2},
        {'occupation': 'Athlete', 'multiplier': 2},
        {'occupation': 'Designer', 'multiplier': 3},
        {'occupation': 'Doctor', 'multiplier': 2},
        {'occupation': 'Hacker', 'multiplier': 2},
    ],
    'Norwegian': [
        {'occupation': 'Fisherman', 'multiplier': 3},
        {'occupation': 'Sailor', 'multiplier': 2},
        {'occupation': 'Explorer', 'multiplier': 3},
        {'occupation': 'Ski', 'multiplier': 4},
        {'occupation': 'Oil Rig', 'multiplier': 4},
        {'occupation': 'Rescue', 'multiplier': 2},
    ],
    'Dutch': [
        {'occupation': 'Sailor', 'multiplier': 2},
        {'occupation': 'Banker', 'multiplier': 2},
        {'occupation': 'Trader', 'multiplier': 2},
        {'occupation': 'Engineer', 'multiplier': 2},
        {'occupation': 'Farmer', 'multiplier': 2},
        {'occupation': 'Smuggler', 'multiplier': 2},
    ],
    'Portuguese': [
        {'occupation': 'Fisherman', 'multiplier': 2},
        {'occupation': 'Sailor', 'multiplier': 2},
        {'occupation': 'Explorer', 'multiplier': 3},
        {'occupation': 'Chef', 'multiplier': 2},
        {'occupation': 'Mason', 'multiplier': 2},
    ],
    'Ukrainian': [
        {'occupation': 'Soldier', 'multiplier': 3},
        {'occupation': 'Farmer', 'multiplier': 2},
        {'occupation': 'Dancer', 'multiplier': 2},
        {'occupation': 'Scientist', 'multiplier': 2},
        {'occupation': 'Sniper', 'multiplier': 3},
        {'occupation': 'Construction', 'multiplier': 2},
    ],
    'Japanese': [
        {'occupation': 'Yakuza', 'multiplier': 4},
        {'occupation': 'Geisha', 'multiplier': 5},
        {'occupation': 'Samurai', 'multiplier': 5},
        {'occupation': 'Ninja', 'multiplier': 5},
        {'occupation': 'Programmer', 'multiplier': 2},
        {'occupation': 'Hacker', 'multiplier': 2},
        {'occupation': 'Salaryman', 'multiplier': 3},
        {'occupation': 'Hikikomori', 'multiplier': 4},
    ],
    'Korean': [
        {'occupation': 'Tech', 'multiplier': 2},
        {'occupation': 'Programmer', 'multiplier': 2},
        {'occupation': 'Doctor', 'multiplier': 2},
        {'occupation': 'Businessman', 'multiplier': 2},
        {'occupation': 'Hacker', 'multiplier': 2},
    ],
    'Brazilian': [
        {'occupation': 'Soccer', 'multiplier': 4},
        {'occupation': 'Dancer', 'multiplier': 3},
        {'occupation': 'Farmer', 'multiplier': 2},
        {'occupation': 'Musician', 'multiplier': 2},
        {'occupation': 'Construction', 'multiplier': 2},
    ],
    'Czech': [
        {'occupation': 'Brewer', 'multiplier': 4},
        {'occupation': 'Glass', 'multiplier': 3},
        {'occupation': 'Musician', 'multiplier': 2},
        {'occupation': 'Dancer', 'multiplier': 2},
        {'occupation': 'Pilot', 'multiplier': 2},
    ],
}

for country, boosts in BOOSTS.items():
    if country in nats:
        n = nats[country]
        n['occupation_boosts'] = boosts
        print(f'{country}: {len(boosts)} occupation boosts added')
    else:
        print(f'WARNING: {country} not found!')

# Save
with open(TEAM_GEN, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('\nDONE!')
