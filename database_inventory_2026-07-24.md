# Database inventory

- Source: `C:\Users\lt-admin\PycharmProjects\TourFemmes\instance\tour_femmes.sqlite3`
- Generated: `2026-07-24T10:19:07`

## Table counts
| table | rows |
| --- | --- |
| award | 0 |
| event | 1 |
| event_entry | 2 |
| event_rider | 35 |
| live_update | 0 |
| rider | 35 |
| stage | 9 |
| stage_lineup | 1 |
| stage_lineup_rider | 6 |
| stage_result | 0 |
| team | 14 |
| team_selection | 1 |
| team_selection_rider | 11 |
| user | 2 |
| user_stage_score | 1 |

## Users
| id | username | email | created_at |
| --- | --- | --- | --- |
| 1 | demo | demo@example.com | 2026-07-19 15:08:34.441431 |
| 2 | marianne | marianne@example.com | 2026-07-19 15:08:34.441431 |

## Events
| id | name | slug | year | budget | team_size | lineup_size | status | pcs_url | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Demo Tour Femmes | demo-tour-femmes | 2026 | 65 | 11 | 6 | active | https://www.procyclingstats.com/race/tour-de-france-femmes/2026 | 2026-07-19 15:08:34.433319 | 2026-07-20 19:09:48.321065 |

## Stages
| id | event_id | number | name | starts_at | distance_km | profile_score | vertical_meters | parcours_type | departure | arrival | is_finished | pcs_url | live_url | profile_image_url | results_imported_at | live_imported_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | Lausanne › Lausanne | 2026-08-01 14:40:00.000000 | 137.0 | 63 | 1403 | Gradient final km | Lausanne | Lausanne | 0 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-1 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-1/live | https://www.procyclingstats.com/images/profiles/ca/ad/tour-de-france-femmes-2026-stage-1-profile.jpg | 2026-07-20 19:55:20.848567 |  |
| 2 | 1 | 2 | Aigle › Genève | 2026-08-02 14:30:00.000000 | 149.0 | 60 | 1721 | Gradient final km | Aigle | Genève | 0 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-2 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-2/live | https://www.procyclingstats.com/images/profiles/ca/cd/tour-de-france-femmes-2026-stage-2-profile.jpg |  |  |
| 3 | 1 | 3 | Genève › Poligny | 2026-08-03 13:45:00.000000 | 157.0 | 70 | 2444 | Gradient final km | Genève | Poligny | 0 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-3 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-3/live | https://www.procyclingstats.com/images/profiles/ca/bc/tour-de-france-femmes-2026-stage-3-profile.jpg |  |  |
| 4 | 1 | 4 | Gevrey-Chambertin › Dijon | 2026-08-04 14:34:00.000000 | 21.0 | 23 | 265 | Gradient final km | Gevrey-Chambertin | Dijon | 0 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-4 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-4/live | https://www.procyclingstats.com/images/profiles/ca/dc/tour-de-france-femmes-2026-stage-4-profile.jpg |  |  |
| 5 | 1 | 5 | Mâcon › Belleville-en-Beaujolais | 2026-08-05 14:00:00.000000 | 140.0 | 131 | 2783 | Gradient final km | Mâcon | Belleville-en-Beaujolais | 0 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-5 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-5/live | https://www.procyclingstats.com/images/profiles/ca/de/tour-de-france-femmes-2026-stage-5-profile.jpg |  |  |
| 6 | 1 | 6 | Montbrison › Tournon-sur-Rhône | 2026-08-06 13:45:00.000000 | 153.0 | 87 | 2574 | Gradient final km | Montbrison | Tournon-sur-Rhône | 0 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-6 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-6/live | https://www.procyclingstats.com/images/profiles/ca/fc/tour-de-france-femmes-2026-stage-6-profile.jpg |  |  |
| 7 | 1 | 7 | La Voulte-sur-Rhône › Mont Ventoux | 2026-08-07 13:15:00.000000 | 144.0 | 354 | 3369 | Gradient final km | La Voulte-sur-Rhône | Mont Ventoux | 0 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-7 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-7/live | https://www.procyclingstats.com/images/profiles/ca/cc/tour-de-france-femmes-2026-stage-7-profile.jpg |  |  |
| 8 | 1 | 8 | Sisteron › Nice | 2026-08-08 13:55:00.000000 | 175.0 | 71 | 1864 | Gradient final km | Sisteron | Nice | 0 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-8 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-8/live | https://www.procyclingstats.com/images/profiles/ca/bc/tour-de-france-femmes-2026-stage-8-profile.jpg |  |  |
| 9 | 1 | 9 | Nice › Nice | 2026-08-09 16:10:00.000000 | 99.0 | 173 | 2338 | Gradient final km | Nice | Nice | 0 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-9 | https://www.procyclingstats.com/race/tour-de-france-femmes/2026/stage-9/live | https://www.procyclingstats.com/images/profiles/ca/db/tour-de-france-femmes-2026-stage-9-profile.jpg |  |  |

## Teams
| id | event_id | name | category | rider_count | pcs_url | image_url |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | 1 | AG Insurance - Soudal Team (WTW) | WTW | 1 | https://www.procyclingstats.com/team/ag-insurance-soudal-team-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/ag-insurance-soudal-team-2026.png |
| 12 | 1 | Cofidis Women Team (PRW) | PRW | 4 | https://www.procyclingstats.com/team/cofidis-women-team-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/cofidis-women-team-2026-n2.png |
| 5 | 1 | EF Education-Oatly (WTW) | WTW | 3 | https://www.procyclingstats.com/team/ef-education-oatly-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/ef-education-oatly-2026-n2.png |
| 1 | 1 | FDJ United - SUEZ (WTW) | WTW | 3 | https://www.procyclingstats.com/team/fdj-united-suez-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/fdj-united-suez-2026-n2.png |
| 6 | 1 | Fenix-Premier Tech (WTW) | WTW | 1 | https://www.procyclingstats.com/team/fenix-premier-tech-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/fenix-premier-tech-2026.png |
| 7 | 1 | Lidl - Trek (WTW) | WTW | 2 | https://www.procyclingstats.com/team/lidl-trek-women-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/lidl-trek-women-2026.png |
| 8 | 1 | Liv AlUla Jayco (WTW) | WTW | 1 | https://www.procyclingstats.com/team/liv-alula-jayco-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/liv-alula-jayco-2026.png |
| 13 | 1 | Ma Petite Entreprise (PRW) | PRW | 7 | https://www.procyclingstats.com/team/ma-petite-entreprise-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/ma-petite-entreprise-2026.png |
| 14 | 1 | Mayenne Monbana My Pie (PRW) | PRW | 1 | https://www.procyclingstats.com/team/mayenne-monbana-my-pie-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/mayenne-monbana-my-pie-2026.png |
| 9 | 1 | Movistar Team (WTW) | WTW | 2 | https://www.procyclingstats.com/team/movistar-women-team-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/movistar-women-team-2026-n2.png |
| 10 | 1 | Team Picnic PostNL (WTW) | WTW | 1 | https://www.procyclingstats.com/team/team-picnic-postnl-women-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/team-picnic-postnl-women-2026.png |
| 2 | 1 | Team SD Worx - Protime (WTW) | WTW | 2 | https://www.procyclingstats.com/team/team-sd-worx-protime-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/team-sd-worx-protime-2026.png |
| 3 | 1 | Team Visma \| Lease a Bike (WTW) | WTW | 3 | https://www.procyclingstats.com/team/team-visma-lease-a-bike-women-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/team-visma-lease-a-bike-women-2026-n2.png |
| 11 | 1 | UAE Team ADQ (WTW) | WTW | 4 | https://www.procyclingstats.com/team/uae-team-adq-2026 | https://www.procyclingstats.com/images/shirts/bx/eb/uae-team-adq-2026.png |

## Event riders
| id | event_id | rider_id | rider_name | team_name | price | active | frozen | startlist_status | imported_at | pcs_slug | pcs_url | photo_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | Demi Vollering | FDJ United - SUEZ (WTW) | 11 | 1 | 0 | listed | 2026-07-20 19:09:49.109781 | demi-vollering | https://www.procyclingstats.com/rider/demi-vollering | https://www.procyclingstats.com/images/riders/uu/dq/demi-vollering-2008.png |
| 4 | 1 | 4 | Pauline Ferrand-Prévot | Team Visma \| Lease a Bike (WTW) | 10 | 1 | 0 | listed | 2026-07-20 19:09:49.190651 | pauline-ferrand-prevot | https://www.procyclingstats.com/rider/pauline-ferrand-prevot | https://www.procyclingstats.com/images/riders/vg/dq/pauline-ferrand-prevot-2026.jpg |
| 5 | 1 | 5 | Elisa Longo Borghini | UAE Team ADQ (WTW) | 8 | 1 | 0 | listed | 2026-07-20 19:09:49.231676 | elisa-longo-borghini | https://www.procyclingstats.com/rider/elisa-longo-borghini | https://www.procyclingstats.com/images/riders/td/dq/elisa-longo-borghini-2026.jpeg |
| 2 | 1 | 2 | Lotte Kopecky | Team SD Worx - Protime (WTW) | 8 | 1 | 0 | listed | 2026-07-20 19:09:49.176744 | lotte-kopecky | https://www.procyclingstats.com/rider/lotte-kopecky | https://www.procyclingstats.com/images/riders/qr/dq/lotte-kopecky-2026-n2-n3.png |
| 22 | 1 | 22 | Paula Blasi | UAE Team ADQ (WTW) | 8 | 1 | 0 | listed | 2026-07-20 19:09:49.213042 | paula-blasi | https://www.procyclingstats.com/rider/paula-blasi | https://www.procyclingstats.com/images/riders/td/dq/paula-blasi-2026.jpeg |
| 20 | 1 | 20 | Anna van der Breggen | Team SD Worx - Protime (WTW) | 7 | 1 | 0 | listed | 2026-07-20 19:09:49.182638 | anna-van-der-breggen | https://www.procyclingstats.com/rider/anna-van-der-breggen | https://www.procyclingstats.com/images/riders/qr/dq/anna-van-der-breggen-2026-n2-n3.png |
| 17 | 1 | 17 | Elisa Balsamo | Lidl - Trek (WTW) | 7 | 1 | 0 | listed | 2026-07-20 19:09:49.137770 | elisa-balsamo | https://www.procyclingstats.com/rider/elisa-balsamo | https://www.procyclingstats.com/images/riders/my/dq/elisa-balsamo-2026.jpg |
| 11 | 1 | 11 | Kim Le Court-Pienaar | AG Insurance - Soudal Team (WTW) | 7 | 1 | 0 | listed | 2026-07-20 19:09:49.058888 | kim-le-court-pienaar | https://www.procyclingstats.com/rider/kim-le-court-pienaar | https://www.procyclingstats.com/images/riders/xk/dq/kimberley-le-court-2026.jpg |
| 3 | 1 | 3 | Marianne Vos | Team Visma \| Lease a Bike (WTW) | 7 | 1 | 0 | listed | 2026-07-20 19:09:49.197597 | marianne-vos | https://www.procyclingstats.com/rider/marianne-vos | https://www.procyclingstats.com/images/riders/vg/dq/marianne-vos-2026.jpg |
| 19 | 1 | 19 | Marlen Reusser | Movistar Team (WTW) | 7 | 1 | 0 | listed | 2026-07-20 19:09:49.157169 | marlen-reusser | https://www.procyclingstats.com/rider/marlen-reusser | https://www.procyclingstats.com/images/riders/kb/dq/marlen-reusser-2026.png |
| 6 | 1 | 6 | Puck Pieterse | Fenix-Premier Tech (WTW) | 7 | 1 | 0 | listed | 2026-07-20 19:09:49.129726 | puck-pieterse | https://www.procyclingstats.com/rider/puck-pieterse | https://www.procyclingstats.com/images/riders/nk/dq/puck-pieterse-2026-n2-n3.jpg |
| 16 | 1 | 16 | Juliette Berthet | FDJ United - SUEZ (WTW) | 6 | 1 | 0 | listed | 2026-07-20 19:09:49.116306 | juliette-labous | https://www.procyclingstats.com/rider/juliette-labous | https://www.procyclingstats.com/images/riders/uu/dq/juliette-labous-2026.jpg |
| 8 | 1 | 8 | Niamh Fisher-Black | Lidl - Trek (WTW) | 6 | 1 | 0 | listed | 2026-07-20 19:09:49.143933 | niamh-fisher-black | https://www.procyclingstats.com/rider/niamh-fisher-black | https://www.procyclingstats.com/images/riders/my/dq/niamh-fisher-black-2026.jpg |
| 7 | 1 | 7 | Cédrine Kerbaol | EF Education-Oatly (WTW) | 5 | 1 | 0 | listed | 2026-07-20 19:09:49.077668 | cedrine-kerbaol | https://www.procyclingstats.com/rider/cedrine-kerbaol | https://www.procyclingstats.com/images/riders/ux/dq/cedrine-kerbaol-2026.jpg |
| 13 | 1 | 13 | Kristen Faulkner | EF Education-Oatly (WTW) | 5 | 1 | 0 | listed | 2026-07-20 19:09:49.070955 | kristen-faulkner | https://www.procyclingstats.com/rider/kristen-faulkner | https://www.procyclingstats.com/images/riders/ux/dq/kristen-faulkner-2026.jpg |
| 12 | 1 | 12 | Maeva Squiban | UAE Team ADQ (WTW) | 5 | 1 | 0 | listed | 2026-07-20 19:09:49.219034 | maeva-squiban | https://www.procyclingstats.com/rider/maeva-squiban | https://www.procyclingstats.com/images/riders/sk/dq/maeva-squiban-2026-n2.jpeg |
| 15 | 1 | 15 | Célia Gery | FDJ United - SUEZ (WTW) | 4 | 1 | 0 | listed | 2026-07-20 19:09:49.098184 | celia-gery | https://www.procyclingstats.com/rider/celia-gery | https://www.procyclingstats.com/images/riders/uu/dq/celia-gery-2008.png |
| 9 | 1 | 9 | Liane Lippert | Movistar Team (WTW) | 4 | 1 | 0 | listed | 2026-07-20 19:09:49.161702 | liane-lippert | https://www.procyclingstats.com/rider/liane-lippert | https://www.procyclingstats.com/images/riders/kb/dq/liane-lippert-2026.png |
| 14 | 1 | 14 | Magdeleine Vallieres | EF Education-Oatly (WTW) | 4 | 1 | 0 | listed | 2026-07-20 19:09:49.090768 | magdeleine-vallieres | https://www.procyclingstats.com/rider/magdeleine-vallieres | https://www.procyclingstats.com/images/riders/ux/dq/magdeleine-vallieres-2026.jpg |
| 18 | 1 | 18 | Monica Trinca Colonel | Liv AlUla Jayco (WTW) | 4 | 1 | 0 | listed | 2026-07-20 19:09:49.149206 | monica-trinca-colonel | https://www.procyclingstats.com/rider/monica-trinca-colonel | https://www.procyclingstats.com/images/riders/nd/dq/monica-trinca-colonel-2026.jpg |
| 23 | 1 | 23 | Silvia Persico | UAE Team ADQ (WTW) | 4 | 1 | 0 | listed | 2026-07-20 19:09:49.240697 | silvia-persico | https://www.procyclingstats.com/rider/silvia-persico | https://www.procyclingstats.com/images/riders/td/dq/silvia-persico-2026.jpeg |
| 25 | 1 | 25 | Victoire Berteau | Cofidis Women Team (PRW) | 4 | 1 | 0 | listed | 2026-07-20 19:09:49.255461 | victoire-berteau | https://www.procyclingstats.com/rider/victoire-berteau | https://www.procyclingstats.com/images/riders/hh/dq/victoire-berteau-2026.jpg |
| 24 | 1 | 24 | Amalie Dideriksen | Cofidis Women Team (PRW) | 3 | 1 | 0 | listed | 2026-07-20 19:09:49.246249 | amalie-dideriksen | https://www.procyclingstats.com/rider/amalie-dideriksen | https://www.procyclingstats.com/images/riders/hh/dq/amalie-dideriksen-2026.jpg |
| 21 | 1 | 21 | Femke de Vries | Team Visma \| Lease a Bike (WTW) | 3 | 1 | 0 | listed | 2026-07-20 19:09:49.206496 | femke-de-vries | https://www.procyclingstats.com/rider/femke-de-vries | https://www.procyclingstats.com/images/riders/vg/dq/femke-de-vries-2026.jpg |
| 26 | 1 | 26 | Julie Bego | Cofidis Women Team (PRW) | 3 | 1 | 0 | listed | 2026-07-20 19:09:49.262509 | julie-bego | https://www.procyclingstats.com/rider/julie-bego | https://www.procyclingstats.com/images/riders/hh/dq/julie-bego-2026.jpg |
| 27 | 1 | 27 | Mijntje Geurts | Cofidis Women Team (PRW) | 3 | 1 | 0 | listed | 2026-07-20 19:09:49.272859 | mijntje-geurts | https://www.procyclingstats.com/rider/mijntje-geurts | https://www.procyclingstats.com/images/riders/hh/dq/mijntje-geurts-2026.jpg |
| 10 | 1 | 10 | Rachele Barbieri | Team Picnic PostNL (WTW) | 3 | 1 | 0 | listed | 2026-07-20 19:09:49.167721 | rachele-barbieri | https://www.procyclingstats.com/rider/rachele-barbieri | https://www.procyclingstats.com/images/riders/dw/dq/rachele-barbieri-2026.jpg |
| 30 | 1 | 30 | Alison Avoine | Ma Petite Entreprise (PRW) | 2 | 1 | 0 | listed | 2026-07-20 19:09:49.299858 | alison-avoine | https://www.procyclingstats.com/rider/alison-avoine | https://www.procyclingstats.com/images/riders/vg/dq/alison-avoine-2026.jpeg |
| 32 | 1 | 32 | Clémence Latimier | Ma Petite Entreprise (PRW) | 2 | 1 | 0 | listed | 2026-07-20 19:09:49.315948 | clemence-latimier | https://www.procyclingstats.com/rider/clemence-latimier | https://www.procyclingstats.com/images/riders/vg/dq/clemence-latimier-2026.jpeg |
| 33 | 1 | 33 | Célia Le Mouël | Ma Petite Entreprise (PRW) | 2 | 1 | 0 | listed | 2026-07-20 19:09:49.329604 | celia-le-mouel | https://www.procyclingstats.com/rider/celia-le-mouel | https://www.procyclingstats.com/images/riders/vg/dq/celia-le-mouel-2026.jpeg |
| 29 | 1 | 29 | Laura Asencio | Ma Petite Entreprise (PRW) | 2 | 1 | 0 | listed | 2026-07-20 19:09:49.291505 | laura-asencio | https://www.procyclingstats.com/rider/laura-asencio | https://www.procyclingstats.com/images/riders/vg/dq/laura-asencio-2026.jpeg |
| 31 | 1 | 31 | Morgane Coston | Ma Petite Entreprise (PRW) | 2 | 1 | 0 | listed | 2026-07-20 19:09:49.309387 | morgane-coston | https://www.procyclingstats.com/rider/morgane-coston | https://www.procyclingstats.com/images/riders/vg/dq/morgane-coston-2026.jpeg |
| 28 | 1 | 28 | Noémie Abgrall | Ma Petite Entreprise (PRW) | 2 | 1 | 0 | listed | 2026-07-20 19:09:49.280950 | noemie-abgrall | https://www.procyclingstats.com/rider/noemie-abgrall | https://www.procyclingstats.com/images/riders/cx/dq/noemie-abgrall-2026-n2-n3.jpeg |
| 34 | 1 | 34 | Océane Mahé | Ma Petite Entreprise (PRW) | 2 | 1 | 0 | listed | 2026-07-20 19:09:49.343530 | oceane-mahe | https://www.procyclingstats.com/rider/oceane-mahe | https://www.procyclingstats.com/images/riders/vg/dq/oceane-mahe-2026.jpeg |
| 35 | 1 | 35 | Francesca Hall | Mayenne Monbana My Pie (PRW) |  | 1 | 0 | listed | 2026-07-20 19:09:49.354352 | francesca-hall | https://www.procyclingstats.com/rider/francesca-hall |  |

## Rider details
### Alison Avoine (id 30)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alison-avoine | https://www.procyclingstats.com/rider/alison-avoine | https://www.procyclingstats.com/images/riders/vg/dq/alison-avoine-2026.jpeg | France | 5th January 2000 | 1.75 |  | 2026-07-19 15:29:29.446007 | 2026-07-20 19:10:33.157614 |

- specialties: `{"Climber": 0, "GC": 47, "Hills": 9, "Onedayraces": 101, "Sprint": 28, "TT": 5}`
- best_results: `["11th Surf Coast Classic ('25)", "13th Schwalbe Women's One Day Classic ('25)", "14th La Classique Morbihan ('26)", "18th Omloop van het Hageland ('25)", "10th La Picto - Charentaise ('23)", "12th La Picto - Charentaise ('21)", "15th KOM Bretagne Ladies Tour CERATIZIT ('23)", "23rd Nokere Koerse WE ('25)", "28th GC RideLondon Classique ('24)", "2x 17th National Championships France WE - ITT ('25, '24)", "17th stage Bretagne Ladies Tour ('26)", "22nd stage UAE Tour Women ('25)"]`
- grand_tour_results: `{"Tour de France Femmes": ["2025: GC 123", "2024: DNF", "2022: GC 108"]}`

### Amalie Dideriksen (id 24)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| amalie-dideriksen | https://www.procyclingstats.com/rider/amalie-dideriksen | https://www.procyclingstats.com/images/riders/hh/dq/amalie-dideriksen-2026.jpg | Denmark | 24th May 1996 | 1.75 | 62.0 | 2026-07-19 15:29:29.077459 | 2026-07-20 19:11:33.130341 |

- specialties: `{"Climber": 40, "GC": 288, "Hills": 520, "Onedayraces": 2110, "Sprint": 1355, "TT": 297}`
- best_results: `["World Championships WE - Road Race ('16)", "Ronde van Drenthe ('17)", "3x stage Boels Rental Ladies Tour ('18, '16)", "stage OVO Energy Women's Tour ('18)", "GP Schellebelle ('23)", "R\u00e9gion Pays de la Loire Tour - F\u00e9minin ('26)", "6x National Championships Denmark WE - Road Race ('26, '21, '19, '18, '15, '14)", "3rd World Championships WE - Road Race ('17)", "National Championships Denmark WE - ITT ('20)", "2nd Trofee Maarten Wynants ('23)", "stage Lotto Belgium Tour ('15)", "3x 2nd National Championships Denmark WE - Road Race ('25, '24, '16)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2023: GC 121, 1 top-10", "2022: GC 94", "2017: GC 68, 3 top-10s", "2016: GC 37, 1 top-10"], "Tour de France Femmes": ["2025: GC 73"], "Vuelta Espa\u00f1a Femenina": ["2025: GC 93", "2022: GC 94", "2021: GC 103", "2016: GC 19"]}`

### Anna van der Breggen (id 20)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anna-van-der-breggen | https://www.procyclingstats.com/rider/anna-van-der-breggen | https://www.procyclingstats.com/images/riders/qr/dq/anna-van-der-breggen-2026-n2-n3.png | Netherlands | 18th April 1990 | 1.68 | 56.0 | 2026-07-19 15:29:28.586895 | 2026-07-20 19:13:59.957632 |

- specialties: `{"Climber": 3775, "GC": 4146, "Hills": 4124, "Onedayraces": 9714, "Sprint": 362, "TT": 5452}`
- best_results: `["7x La Fl\u00e8che Wallonne F\u00e9minine ('21, '20, '19, '18, '17, '16, '15)", "2x World Championships WE - Road Race ('20, '18)", "4x GC Giro d'Italia Internazionale Femminile ('21, '20, '17, '15)", "2x Li\u00e8ge-Bastogne-Li\u00e8ge Femmes ('18, '17)", "Olympic Games WE - Road Race ('16)", "2x GC Amgen Tour of California Women\u2019s Race empowered wi ('19, '17)", "Ronde van Vlaanderen WE ('18)", "Strade Bianche Donne ('18)", "Amstel Gold Race Ladies Edition ('17)", "GC Vuelta a Burgos Feminas ('21)", "Classic Lorient Agglom\u00e9ration ('19)", "World Championships WE - ITT ('20)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 3, 1 stage win, 4 top-10s", "2025: GC 6, 4 top-10s", "2021: GC 1, 2 stage wins, 5 top-10s", "2020: GC 1, 4 top-10s", "2019: GC 2, 1 stage win, 6 top-10s", "2017: GC 1, 5 top-10s", "2016: GC 3, 6 top-10s", "2015: GC 1, 1 stage win, 7 top-10s", "2014: GC 3, 6 top-10s", "2013: GC 18, 3 top-10s", "2012: GC 22", "2011: GC 89", "2010: GC 43", "2009: DNF"], "Tour de France Femmes": ["2025: GC 11, 4 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2026: GC 2, 1 stage win, 4 top-10s", "2025: GC 3, 1 stage win, 3 top-10s", "2021: GC 58"]}`

### Clémence Latimier (id 32)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clemence-latimier | https://www.procyclingstats.com/rider/clemence-latimier | https://www.procyclingstats.com/images/riders/vg/dq/clemence-latimier-2026.jpeg | France | 24th August 2003 | 1.78 |  | 2026-07-19 15:29:29.580126 | 2026-07-20 19:12:41.127404 |

- specialties: `{"Climber": 226, "GC": 152, "Hills": 150, "Onedayraces": 130, "Sprint": 6, "TT": 0}`
- best_results: `["2nd Alpes Gresivaudan Classic ('26)", "4th GC Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('26)", "13th GC Tour de Suisse Women ('26)", "9th Grand Prix F\u00e9minin de Chamb\u00e9ry ('26)", "10th Pionera Race ('26)", "6th stage Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('26)", "12th Alpes Gresivaudan Classic ('25)", "2x 6th National Championships France WE - Road Race ('26, '25)", "16th Grand Prix F\u00e9minin de Chamb\u00e9ry ('24)", "21st GC Setmana Ciclista Valenciana - Vuelta Comunitat V ('26)", "7th KOM Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('26)", "8th stage Trofeo Ponente in Rosa ('24)"]`
- grand_tour_results: `{"Tour de France Femmes": ["2025: GC 61"]}`

### Cédrine Kerbaol (id 7)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cedrine-kerbaol | https://www.procyclingstats.com/rider/cedrine-kerbaol | https://www.procyclingstats.com/images/riders/ux/dq/cedrine-kerbaol-2026.jpg | France | 15th May 2001 | 1.66 | 57.0 | 2026-07-19 15:08:34.523181 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 800, "GC": 1432, "Hills": 1604, "Onedayraces": 1081, "Sprint": 108, "TT": 782}`
- best_results: `["Tre Valli Varesine Women's Race ('24)", "GC Tour de Normandie F\u00e9minin ('23)", "stage Tour de France Femmes ('24)", "Durango - Durango Emakumeen Saria ('24)", "Vuelta CV Feminas ('24)", "stage Vuelta Espa\u00f1a Femenina ('26)", "2nd GC Tour de Suisse Women ('26)", "2x National Championships France WE - ITT ('25, '23)", "stage Tour de Normandie F\u00e9minin ('23)", "2nd GC Bretagne Ladies Tour CERATIZIT ('22)", "2nd Grand Prix du Morbihan F\u00e9minin ('23)", "Chrono \u00abRoland bouge !\u00bb ('24)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2024: DNF, 1 top-10"], "Tour de France Femmes": ["2025: GC 8, 3 top-10s", "2024: GC 6, 1 stage win, 4 top-10s", "2023: GC 12"], "Vuelta Espa\u00f1a Femenina": ["2026: GC 18, 1 stage win, 1 top-10", "2025: GC 4, 4 top-10s"]}`

### Célia Gery (id 15)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| celia-gery | https://www.procyclingstats.com/rider/celia-gery | https://www.procyclingstats.com/images/riders/uu/dq/celia-gery-2008.png | France | 4th January 2006 |  |  | 2026-07-19 15:29:25.858009 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 142, "GC": 103, "Hills": 334, "Onedayraces": 441, "Sprint": 106, "TT": 3}`
- best_results: `["De Brabantse Pijl - La Fl\u00e8che Braban\u00e7onne WE ('26)", "Grand Prix F\u00e9minin de Chamb\u00e9ry ('26)", "stage Giro d'Italia Women ('26)", "2nd GC Volta Ciclista a Catalunya Femenina ('26)", "National Championships France WE - Road Race ('26)", "2nd stage Volta Ciclista a Catalunya Femenina ('26)", "4th Giro dell'Appennino Donne ('26)", "4th Pointe du Raz Ladies Classic ('25)", "4th stage Giro d'Italia Women ('26)", "9th Trofeo Alfredo Binda - Comune di Cittiglio ('26)", "11th Paris-Roubaix Femmes ('26)", "7th Grand Prix du Morbihan F\u00e9minin ('25)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 29, 1 stage win, 4 top-10s", "2025: DNF"]}`

### Célia Le Mouël (id 33)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| celia-le-mouel | https://www.procyclingstats.com/rider/celia-le-mouel | https://www.procyclingstats.com/images/riders/vg/dq/celia-le-mouel-2026.jpeg | France | 20th July 2000 |  |  | 2026-07-19 15:29:29.644316 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 158, "GC": 111, "Hills": 394, "Onedayraces": 178, "Sprint": 49, "TT": 445}`
- best_results: `["National Championships France WE - ITT ('26)", "6th Grand Prix du Morbihan F\u00e9minin ('26)", "6th Grand Prix Presidente ('25)", "2x 5th stage Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('24)", "9th GC Bretagne Ladies Tour CERATIZIT ('22)", "10th Durango - Durango Emakumeen Saria ('25)", "10th Grand Prix du Morbihan F\u00e9minin ('25)", "2x 6th stage Tour El Salvador ('25)", "12th Navarra Women's Elite Classics ('26)", "11th GC Bretagne Ladies Tour ('26)", "8th stage Tour de France Femmes ('23)", "20th GC Tour of Britain Women ('24)"]`
- grand_tour_results: `{"Tour de France Femmes": ["2025: GC 56", "2024: GC 65", "2023: GC 88, 1 top-10"]}`

### Demi Vollering (id 1)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| demi-vollering | https://www.procyclingstats.com/rider/demi-vollering | https://www.procyclingstats.com/images/riders/uu/dq/demi-vollering-2008.png | Netherlands | 15th November 1996 | 1.72 | 57.0 | 2026-07-19 15:08:34.477455 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 3388, "GC": 5996, "Hills": 5728, "Onedayraces": 7800, "Sprint": 576, "TT": 2055}`
- best_results: `["3x Li\u00e8ge-Bastogne-Li\u00e8ge Femmes ('26, '23, '21)", "3x GC Itzulia Women ('25, '24, '22)", "2x GC Vuelta Espa\u00f1a Femenina ('25, '24)", "2x Strade Bianche Donne ('25, '23)", "2x La Fl\u00e8che Wallonne F\u00e9minine ('26, '23)", "2x GC Vuelta a Burgos Feminas ('24, '23)", "GC Tour de France Femmes ('23)", "Ronde van Vlaanderen WE ('26)", "Amstel Gold Race Ladies Edition ('23)", "GC Giro d'Italia Women ('26)", "GC Tour de Romandie F\u00e9minin ('23)", "La Course by Le Tour de France ('21)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 1, 2 stage wins, 4 top-10s", "2021: GC 3, 4 top-10s", "2019: GC 13, 5 top-10s"], "Tour de France Femmes": ["2025: GC 2, 7 top-10s", "2024: GC 2, 2 stage wins, 4 top-10s", "2023: GC 1, 1 stage win, 5 top-10s", "2022: GC 2, 4 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2025: GC 1, 2 stage wins, 3 top-10s", "2024: GC 1, 2 stage wins, 4 top-10s", "2023: GC 2, 2 stage wins, 5 top-10s", "2022: GC 3, 2 top-10s"]}`

### Elisa Balsamo (id 17)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elisa-balsamo | https://www.procyclingstats.com/rider/elisa-balsamo | https://www.procyclingstats.com/images/riders/my/dq/elisa-balsamo-2026.jpg | Italy | 27th February 1998 | 1.71 | 55.0 | 2026-07-19 15:29:27.811591 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 128, "GC": 991, "Hills": 2804, "Onedayraces": 6515, "Sprint": 4031, "TT": 504}`
- best_results: `["3x Trofeo Alfredo Binda - Comune di Cittiglio ('25, '24, '22)", "World Championships WE - Road Race ('21)", "2x Exterioo Classic Brugge-De Panne WE ('24, '22)", "In Flanders Fields - In Wevelgem ('22)", "6x stage Giro d'Italia Donne ('26, '22)", "7x stage Setmana Ciclista Valenciana - Vuelta Comunitat V ('25, '24, '23, '22)", "2x stage Vuelta Espa\u00f1a Femenina ('22, '20)", "2x 2nd In Flanders Fields - In Wevelgem ('25, '24)", "Scheldeprijs WE ('25)", "Gran Premio Bruno Beghelli Internazionale Donne E ('18)", "2x stage Tour de Suisse Women ('25, '22)", "2x 2nd Ronde van Drenthe ('24, '22)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 58, 4 stage wins, 4 top-10s", "2024: DNF, 1 top-10", "2022: GC 49, 2 stage wins, 5 top-10s"], "Tour de France Femmes": ["2025: DNF", "2024: GC 61, 2 top-10s", "2023: DNF, 1 top-10", "2022: GC 37, 3 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2022: GC 30, 1 stage win, 2 top-10s", "2021: GC 28, 3 top-10s", "2020: GC 11, 1 stage win, 2 top-10s", "2019: DNF", "2018: GC 30"]}`

### Elisa Longo Borghini (id 5)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elisa-longo-borghini | https://www.procyclingstats.com/rider/elisa-longo-borghini | https://www.procyclingstats.com/images/riders/td/dq/elisa-longo-borghini-2026.jpeg | Italy | 10th December 1991 | 1.7 | 59.0 | 2026-07-19 15:08:34.511146 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 4302, "GC": 5726, "Hills": 6119, "Onedayraces": 11535, "Sprint": 890, "TT": 3091}`
- best_results: `["3x GC UAE Tour Women ('26, '25, '23)", "2x Ronde van Vlaanderen WE ('24, '15)", "2x GC Giro d'Italia Women ('25, '24)", "2x Trofeo Alfredo Binda - Comune di Cittiglio ('21, '13)", "Paris-Roubaix Femmes ('22)", "Strade Bianche Donne ('17)", "GC Women's Tour ('22)", "4x Giro dell'Emilia Internazionale Donne Elite ('24, '22, '16, '15)", "GC WWT Emakumeen Bira ('19)", "Classic Lorient Agglom\u00e9ration ('21)", "2x De Brabantse Pijl WE ('25, '24)", "2x Tre Valli Varesine Women's Race ('25, '22)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 4, 1 stage win, 6 top-10s", "2025: GC 1, 8 top-10s", "2024: GC 1, 1 stage win, 7 top-10s", "2023: DNF, 1 stage win, 2 top-10s", "2022: GC 4, 6 top-10s", "2021: GC 14, 2 top-10s", "2020: GC 3, 1 stage win, 3 top-10s", "2019: GC 8, 6 top-10s", "2018: GC 10, 3 top-10s", "2017: GC 2, 4 top-10s", "2016: GC 11, 4 top-10s", "2015: GC 8, 3 top-10s", "2014: GC 5, 5 top-10s", "2012: GC 9, 4 top-10s", "2011: GC 18"], "Tour de France Femmes": ["2025: DNF", "2023: DNF, 3 top-10s", "2022: GC 6, 6 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2024: GC 3, 4 top-10s", "2022: GC 2, 3 top-10s", "2021: GC 7, 2 top-10s", "2020: GC 2, 2 top-10s", "2018: GC 8", "2017: GC 52"]}`

### Femke de Vries (id 21)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| femke-de-vries | https://www.procyclingstats.com/rider/femke-de-vries | https://www.procyclingstats.com/images/riders/vg/dq/femke-de-vries-2026.jpg | Netherlands | 16th April 1994 |  |  | 2026-07-19 15:29:28.755624 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 556, "GC": 729, "Hills": 722, "Onedayraces": 226, "Sprint": 122, "TT": 361}`
- best_results: `["stage Tour de Suisse Women ('26)", "3rd GC UAE Tour Women ('26)", "2nd GC Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('25)", "5th GC Tour de Suisse Women ('26)", "6th GC Giro d'Italia Women ('26)", "2nd GC Tour de Feminin ('24)", "2nd stage Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('25)", "2nd stage Baloise Ladies Tour ('23)", "3rd stage UAE Tour Women ('26)", "3rd stage Tour de Suisse Women ('24)", "2nd National Championships Netherlands WE - ITT ('26)", "7th GC Setmana Ciclista Valenciana - Vuelta Comunitat V ('25)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 6, 4 top-10s", "2024: GC 20"], "Tour de France Femmes": ["2025: GC 20", "2024: GC 55"], "Vuelta Espa\u00f1a Femenina": ["2025: GC 51"]}`

### Francesca Hall (id 35)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| francesca-hall | https://www.procyclingstats.com/rider/francesca-hall |  | Great Britain | 11th April 1995 | 1.57 | 47.0 | 2026-07-19 15:29:29.787540 | 2026-07-20 19:12:17.049008 |

- specialties: `{"Climber": 244, "GC": 59, "Hills": 402, "Onedayraces": 216, "Sprint": 10, "TT": 41}`
- best_results: `["Grand Prix San Salvador ('26)", "2nd Grand Prix Longitudinal del Norte ('26)", "2nd Grand Prix el Salvador ('26)", "stage Giro Mediterraneo Rosa ('25)", "stage Tour of the Gila WE ('25)", "2nd GC Giro Mediterraneo Rosa ('25)", "3rd stage Tour El Salvador ('26)", "2nd stage Volta a Portugal Feminina ('24)", "9th Durango - Durango Emakumeen Saria ('26)", "6th GC Volta a Portugal Feminina ('24)", "3rd stage Tour de Bloom ('25)", "11th GC Tour El Salvador ('26)"]`
- grand_tour_results: `{"Vuelta Espa\u00f1a Femenina": ["2026: GC 83"]}`

### Julie Bego (id 26)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| julie-bego | https://www.procyclingstats.com/rider/julie-bego | https://www.procyclingstats.com/images/riders/hh/dq/julie-bego-2026.jpg | France | 9th January 2005 |  |  | 2026-07-19 15:29:29.191035 | 2026-07-20 19:10:52.793194 |

- specialties: `{"Climber": 272, "GC": 65, "Hills": 220, "Onedayraces": 313, "Sprint": 22, "TT": 9}`
- best_results: `["3rd Alpes Gresivaudan Classic ('24)", "4th Trofeo Oro in Euro ('24)", "5th Tre Valli Varesine Women's Race ('24)", "4th Alpes Gresivaudan Classic ('26)", "5th Navarra Women's Elite Classics ('24)", "3rd National Championships France WE - Road Race ('25)", "6th Alpes Gresivaudan Classic ('25)", "7th GC Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('24)", "11th De Brabantse Pijl WE ('24)", "6th stage Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('24)", "22nd GC Tour de Romandie F\u00e9minin ('24)", "14th GC Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('25)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2024: DNF"], "Tour de France Femmes": ["2025: GC 33"]}`

### Juliette Berthet (id 16)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| juliette-labous | https://www.procyclingstats.com/rider/juliette-labous | https://www.procyclingstats.com/images/riders/uu/dq/juliette-labous-2026.jpg | France | 4th November 1998 | 1.65 | 54.0 | 2026-07-19 15:29:27.068795 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 2288, "GC": 3912, "Hills": 2996, "Onedayraces": 2340, "Sprint": 198, "TT": 2107}`
- best_results: `["GC Vuelta a Burgos Feminas ('22)", "stage Giro d'Italia Donne ('22)", "2nd GC Giro d'Italia Donne ('23)", "2nd GC The Women's Tour ('21)", "3rd GC Itzulia Women ('24)", "2x 2nd stage Vuelta a Burgos Feminas ('25, '22)", "4th GC Tour de France Femmes ('22)", "National Championships France WE - ITT ('20)", "National Championships France WE - Road Race ('24)", "2x 3rd Giro dell'Emilia Internazionale Donne Elite ('24, '23)", "2nd stage Tour de France Femmes ('25)", "4th GC Vuelta Espa\u00f1a Femenina ('24)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2025: GC 29, 2 top-10s", "2024: GC 5, 5 top-10s", "2023: GC 2, 3 top-10s", "2022: GC 9, 1 stage win, 3 top-10s", "2021: GC 7, 4 top-10s", "2020: GC 23, 1 top-10", "2019: GC 11, 2 top-10s", "2018: GC 29, 1 top-10"], "Tour de France Femmes": ["2025: GC 7, 2 top-10s", "2024: GC 9, 2 top-10s", "2023: GC 5, 2 top-10s", "2022: GC 4, 3 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2026: GC 5, 2 top-10s", "2025: GC 5, 2 top-10s", "2024: GC 4, 4 top-10s", "2023: GC 7, 2 top-10s", "2022: GC 9, 1 top-10", "2021: DNF, 1 top-10", "2019: GC 19", "2017: GC 59"]}`

### Kim Le Court-Pienaar (id 11)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kim-le-court-pienaar | https://www.procyclingstats.com/rider/kim-le-court-pienaar | https://www.procyclingstats.com/images/riders/xk/dq/kimberley-le-court-2026.jpg | Mauritius | 23rd March 1996 |  |  | 2026-07-19 15:08:34.555108 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 544, "GC": 555, "Hills": 850, "Onedayraces": 1637, "Sprint": 121, "TT": 182}`
- best_results: `["Li\u00e8ge-Bastogne-Li\u00e8ge Femmes ('25)", "African Games WE - Road Race ('15)", "Giro dell'Emilia Internazionale Donne Elite ('25)", "stage Tour de France Femmes ('25)", "stage Giro d'Italia Women ('24)", "stage Tour of Britain Women ('25)", "5x National Championships Mauritius WE - Road Race ('26, '25, '24, '19, '16)", "3x National Championships Mauritius WE - ITT ('26, '25, '24)", "3rd GC UAE Tour Women ('25)", "2x 2nd African Continental Championships WE - Road Race ('22, '17)", "2nd stage Tour de France Femmes ('25)", "4th GC UAE Tour Women ('26)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2024: GC 18, 1 stage win, 4 top-10s", "2016: DNF"], "Tour de France Femmes": ["2025: GC 16, 1 stage win, 5 top-10s", "2024: GC 36, 2 top-10s"]}`

### Kristen Faulkner (id 13)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kristen-faulkner | https://www.procyclingstats.com/rider/kristen-faulkner | https://www.procyclingstats.com/images/riders/ux/dq/kristen-faulkner-2026.jpg | United States | 18th December 1992 | 1.68 | 62.0 | 2026-07-19 15:29:24.373512 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 728, "GC": 825, "Hills": 1010, "Onedayraces": 1169, "Sprint": 284, "TT": 840}`
- best_results: `["Olympic Games WE - Road Race ('24)", "2x stage Giro d'Italia Donne ('22)", "Omloop van het Hageland ('24)", "Pan American Games WE - ITT ('23)", "stage Vuelta Espa\u00f1a Femenina ('24)", "stage Tour of Scandinavia ('21)", "Pan American Championships WE - ITT ('26)", "stage Tour de Suisse Women ('22)", "2nd GC Tour de Suisse Women ('22)", "3rd GC Tour of Scandinavia ('21)", "2x National Championships United States WE - Road Rac ('25, '24)", "3rd GC Itzulia Women ('22)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: DNF", "2022: GC 11, 2 stage wins, 4 top-10s", "2021: DNF"], "Tour de France Femmes": ["2025: DNF", "2024: GC 38, 2 top-10s", "2022: GC 40"], "Vuelta Espa\u00f1a Femenina": ["2026: GC 41", "2025: GC 50", "2024: GC 12, 1 stage win, 3 top-10s", "2023: GC 28", "2022: DNF", "2021: DNF, 1 top-10"]}`

### Laura Asencio (id 29)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| laura-asencio | https://www.procyclingstats.com/rider/laura-asencio | https://www.procyclingstats.com/images/riders/vg/dq/laura-asencio-2026.jpeg | France | 14th May 1998 | 1.57 | 47.0 | 2026-07-19 15:29:29.374404 | 2026-07-20 19:10:26.910638 |

- specialties: `{"Climber": 44, "GC": 150, "Hills": 540, "Onedayraces": 278, "Sprint": 102, "TT": 1}`
- best_results: `["2nd Pionera Race ('26)", "5th Vuelta CV Feminas ('20)", "3rd La Picto - Charentaise ('21)", "12th GC Itzulia Women ('24)", "4th Jeux de la Francophonie WE - Road Race ('17)", "12th Classic Lorient Agglom\u00e9ration ('22)", "9th Grand Prix du Morbihan F\u00e9minin ('18)", "13th Tour of Guangxi ('24)", "3rd stage Premondiale Giro Toscana Int. Femminile - Memorial ('23)", "14th Giro dell'Emilia Internazionale Donne Elite ('23)", "7th GC Premondiale Giro Toscana Int. Femminile - Memorial ('23)", "12th Grand Prix du Morbihan F\u00e9minin ('24)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2024: GC 31"], "Tour de France Femmes": ["2022: GC 57"], "Vuelta Espa\u00f1a Femenina": ["2025: DNF", "2022: GC 37", "2021: DNF", "2020: GC 41, 1 top-10"]}`

### Liane Lippert (id 9)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| liane-lippert | https://www.procyclingstats.com/rider/liane-lippert | https://www.procyclingstats.com/images/riders/kb/dq/liane-lippert-2026.png | Germany | 13th January 1998 | 1.68 | 56.0 | 2026-07-19 15:08:34.541287 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 1471, "GC": 2334, "Hills": 4138, "Onedayraces": 3473, "Sprint": 536, "TT": 703}`
- best_results: `["Cadel Evans Great Ocean Road Race - Elite Women's Race ('20)", "3x stage Giro d'Italia Women ('25, '24)", "Vuelta CV Feminas ('26)", "GC Lotto Belgium Tour ('18)", "Tre Valli Varesine Women's Race ('23)", "stage Tour de France Femmes ('23)", "stage Tour de Romandie F\u00e9minin ('23)", "2nd GC Tour of Scandinavia ('22)", "2nd La Fl\u00e8che Wallonne F\u00e9minine ('23)", "2nd European Continental Championships WE - Road Race ('21)", "2nd GC Santos Women's Tour Down Under ('20)", "3x National Championships Germany WE - Road Race ('23, '22, '18)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2025: GC 30, 2 stage wins, 3 top-10s", "2024: DNF, 1 stage win, 1 top-10", "2023: GC 16, 3 top-10s", "2021: GC 18, 2 top-10s", "2020: GC 13, 4 top-10s", "2018: GC 64"], "Tour de France Femmes": ["2025: GC 59, 2 top-10s", "2024: GC 18, 2 top-10s", "2023: GC 20, 1 stage win, 2 top-10s", "2022: GC 16, 1 top-10"], "Vuelta Espa\u00f1a Femenina": ["2026: GC 21, 3 top-10s", "2025: GC 41, 1 top-10", "2024: GC 31", "2023: GC 21, 1 top-10", "2022: GC 4, 2 top-10s", "2021: GC 5, 3 top-10s", "2020: GC 18", "2018: GC 5"]}`

### Lotte Kopecky (id 2)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lotte-kopecky | https://www.procyclingstats.com/rider/lotte-kopecky | https://www.procyclingstats.com/images/riders/qr/dq/lotte-kopecky-2026-n2-n3.png | Belgium | 10th November 1995 | 1.7 | 65.0 | 2026-07-19 15:08:34.487372 | 2026-07-20 19:12:31.505030 |

- specialties: `{"Climber": 642, "GC": 2800, "Hills": 3339, "Onedayraces": 8506, "Sprint": 4137, "TT": 2213}`
- best_results: `["2x World Championships WE - Road Race ('24, '23)", "3x Ronde van Vlaanderen WE ('25, '23, '22)", "2x Strade Bianche Donne ('24, '22)", "2x GC Simac Ladies Tour ('24, '23)", "Milano-Sanremo Donne ('26)", "Paris-Roubaix Femmes ('24)", "GC Tour de Romandie F\u00e9minin ('24)", "Omloop Het Nieuwsblad WE ('23)", "GC UAE Tour Women ('24)", "3x Nokere Koerse WE ('26, '24, '23)", "GC Tour of Britain Women ('24)", "GC Internationale LOTTO Th\u00fcringen Ladies Tour ('23)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2025: DNF, 3 top-10s", "2024: GC 2, 1 stage win, 7 top-10s", "2022: GC 42, 5 top-10s", "2020: DNF, 1 stage win, 4 top-10s", "2019: GC 86, 1 top-10"], "Tour de France Femmes": ["2025: GC 45", "2023: GC 2, 1 stage win, 7 top-10s", "2022: GC 38, 4 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2026: GC 50, 1 stage win, 4 top-10s", "2022: GC 21, 3 top-10s", "2021: GC 18, 1 stage win, 2 top-10s", "2017: GC 11"]}`

### Maeva Squiban (id 12)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| maeva-squiban | https://www.procyclingstats.com/rider/maeva-squiban | https://www.procyclingstats.com/images/riders/sk/dq/maeva-squiban-2026-n2.jpeg | France | 19th March 2002 | 1.66 |  | 2026-07-19 15:08:34.560623 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 456, "GC": 367, "Hills": 1302, "Onedayraces": 409, "Sprint": 146, "TT": 711}`
- best_results: `["2x stage Tour de France Femmes ('25)", "Trofeo Marratxi-Felanitx ('26)", "2nd GC Setmana Ciclista Valenciana - Vuelta Comunitat V ('26)", "stage Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('24)", "2nd stage Tour de France Femmes ('24)", "3rd GC Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('25)", "2nd stage Setmana Ciclista Valenciana - Vuelta Comunitat V ('26)", "stage Vuelta Extremadura F\u00e9minas ('23)", "2nd stage Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('25)", "2nd National Championships France WE - ITT ('26)", "3rd stage Setmana Ciclista Valenciana - Vuelta Comunitat V ('26)", "3rd GC AG Tour de la Semois ('24)"]`
- grand_tour_results: `{"Tour de France Femmes": ["2025: GC 15, 2 stage wins, 2 top-10s", "2024: GC 40, 1 top-10", "2022: DNF"], "Vuelta Espa\u00f1a Femenina": ["2026: DNF, 1 top-10", "2025: GC 61"]}`

### Magdeleine Vallieres (id 14)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| magdeleine-vallieres | https://www.procyclingstats.com/rider/magdeleine-vallieres | https://www.procyclingstats.com/images/riders/ux/dq/magdeleine-vallieres-2026.jpg | Canada | 10th August 2001 |  |  | 2026-07-19 15:29:25.174419 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 496, "GC": 268, "Hills": 735, "Onedayraces": 1074, "Sprint": 43, "TT": 50}`
- best_results: `["World Championships WE - Road Race ('25)", "Trofeo Palma ('24)", "5th Strade Bianche Donne ('26)", "6th La Fl\u00e8che Wallonne F\u00e9minine ('26)", "2nd National Championships Canada WE - Road Race ('24)", "6th GC Setmana Ciclista Valenciana - Vuelta Comunitat V ('26)", "8th Li\u00e8ge-Bastogne-Li\u00e8ge Femmes ('26)", "7th Giro dell'Emilia Internazionale Donne Elite ('25)", "12th GC Giro d'Italia Women ('26)", "2nd stage Watersley Womens Challenge ('21)", "14th World Championships WE - Road Race ('24)", "13th GC Itzulia Women ('26)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 12, 2 top-10s", "2024: GC 38", "2023: DNF", "2022: GC 38"], "Tour de France Femmes": ["2025: GC 18, 1 top-10", "2024: DNF", "2023: GC 97", "2022: GC 66"], "Vuelta Espa\u00f1a Femenina": ["2025: GC 30", "2024: GC 29, 1 top-10", "2023: GC 60"]}`

### Marianne Vos (id 3)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| marianne-vos | https://www.procyclingstats.com/rider/marianne-vos | https://www.procyclingstats.com/images/riders/vg/dq/marianne-vos-2026.jpg | Netherlands | 13th May 1987 | 1.68 | 58.0 | 2026-07-19 15:08:34.496938 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 4048, "GC": 4618, "Hills": 4964, "Onedayraces": 19832, "Sprint": 3594, "TT": 6792}`
- best_results: `["3x World Championships WE - Road Race ('13, '12, '06)", "5x La Fl\u00e8che Wallonne F\u00e9minine ('13, '11, '09, '08, '07)", "4x Trofeo Alfredo Binda - Comune di Cittiglio ('19, '12, '10, '09)", "3x GC Tour of Scandinavia ('19, '18, '17)", "3x Ronde van Drenthe ('13, '12, '11)", "3x Postnord UCI WWT V\u00e5rg\u00e5rda WestSweden RR ('18, '13, '09)", "Olympic Games WE - Road Race ('12)", "2x Amstel Gold Race Ladies Edition ('24, '21)", "32x stage Giro d'Italia Femminile ('22, '21, '20, '19, '18, '14, '13, '12, '11, '10, '07)", "2x Classic Lorient Agglom\u00e9ration ('13, '12)", "Ronde van Vlaanderen WE ('13)", "6x 2nd World Championships WE - Road Race ('21, '11, '10, '09, '08, '07)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2025: DNF, 2 top-10s", "2023: GC 48, 4 top-10s", "2022: DNF, 2 stage wins, 4 top-10s", "2021: DNF, 2 stage wins, 5 top-10s", "2020: GC 11, 3 stage wins, 4 top-10s", "2019: GC 20, 4 stage wins, 5 top-10s", "2018: DNF, 1 stage win, 4 top-10s", "2014: GC 1, 4 stage wins, 10 top-10s", "2013: GC 6, 3 stage wins, 6 top-10s", "2012: GC 1, 5 stage wins, 8 top-10s", "2011: GC 1, 5 stage wins, 10 top-10s", "2010: GC 7, 2 stage wins, 10 top-10s", "2007: GC 12, 1 stage win, 6 top-10s"], "Tour de France Femmes": ["2025: GC 37, 1 stage win, 5 top-10s", "2024: GC 31, 4 top-10s", "2023: DNF, 3 top-10s", "2022: GC 26, 2 stage wins, 6 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2026: DNF, 1 top-10", "2025: GC 40, 2 stage wins, 4 top-10s", "2024: GC 24, 2 stage wins, 3 top-10s", "2023: GC 26, 2 stage wins, 3 top-10s"]}`

### Marlen Reusser (id 19)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| marlen-reusser | https://www.procyclingstats.com/rider/marlen-reusser | https://www.procyclingstats.com/images/riders/kb/dq/marlen-reusser-2026.png | Switzerland | 20th September 1991 | 1.8 | 70.0 | 2026-07-19 15:29:28.283922 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 1276, "GC": 3188, "Hills": 2385, "Onedayraces": 2287, "Sprint": 354, "TT": 3208}`
- best_results: `["3x GC Tour de Suisse Women ('26, '25, '23)", "GC Vuelta a Burgos Feminas ('25)", "In Flanders Fields - In Wevelgem ('23)", "Dwars door Vlaanderen WE ('26)", "GC Itzulia Women ('23)", "World Championships WE - ITT ('25)", "GC Setmana Ciclista Valenciana - Vuelta Comunitat V ('24)", "5x stage Tour de Suisse Women ('26, '25, '23)", "4x European Continental Championships WE - ITT ('25, '23, '22, '21)", "2x stage Tour de France Femmes ('23, '22)", "2x 2nd GC Vuelta Espa\u00f1a Femenina ('25, '21)", "2x stage Vuelta a Burgos Feminas ('25)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 13, 4 top-10s", "2025: GC 2, 1 stage win, 6 top-10s", "2021: DNF", "2020: DNF"], "Tour de France Femmes": ["2025: DNF", "2023: GC 28, 1 stage win, 2 top-10s", "2022: DNF, 1 stage win, 1 top-10"], "Vuelta Espa\u00f1a Femenina": ["2025: GC 2, 3 top-10s", "2024: GC 13, 1 top-10", "2023: GC 23, 2 top-10s", "2022: GC 29", "2021: GC 2, 1 stage win, 3 top-10s"]}`

### Mijntje Geurts (id 27)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mijntje-geurts | https://www.procyclingstats.com/rider/mijntje-geurts | https://www.procyclingstats.com/images/riders/hh/dq/mijntje-geurts-2026.jpg | Netherlands | 25th October 2003 |  |  | 2026-07-19 15:29:29.253405 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 96, "GC": 39, "Hills": 208, "Onedayraces": 143, "Sprint": 2, "TT": 42}`
- best_results: `["10th La Fl\u00e8che Wallonne F\u00e9minine ('25)", "7th Grand Prix du Morbihan F\u00e9minin ('26)", "20th Amstel Gold Race Ladies Edition ('23)", "21st La Fl\u00e8che Wallonne F\u00e9minine ('23)", "9th GC Tour de Feminin ('23)", "4th KOM Giro d'Italia Women ('25)", "21st GC Internationale LOTTO Th\u00fcringen Ladies Tour ('22)", "6th stage Tour de Feminin ('23)", "7th stage Tour de Feminin ('23)", "9th Points GC Tour de Feminin ('23)", "11th GC Princess Anna Vasa Tour ('24)", "12th GC AG Tour de la Semois ('23)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2025: GC 76", "2024: DNF"]}`

### Monica Trinca Colonel (id 18)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| monica-trinca-colonel | https://www.procyclingstats.com/rider/monica-trinca-colonel | https://www.procyclingstats.com/images/riders/nd/dq/monica-trinca-colonel-2026.jpg | Italy | 21st May 1999 |  |  | 2026-07-19 15:29:28.213266 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 745, "GC": 860, "Hills": 945, "Onedayraces": 607, "Sprint": 38, "TT": 410}`
- best_results: `["GC Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('25)", "2nd GC UAE Tour Women ('26)", "stage Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('25)", "4th GC UAE Tour Women ('25)", "2nd stage UAE Tour Women ('26)", "3rd GC Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('24)", "2x 7th GC Vuelta Espa\u00f1a Femenina ('26, '25)", "2x 2nd National Championships Italy WE - Road Race ('26, '25)", "8th Li\u00e8ge-Bastogne-Li\u00e8ge Femmes ('25)", "6th Tre Valli Varesine Women's Race ('25)", "2x 3rd stage Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('25)", "4th stage Vuelta Espa\u00f1a Femenina ('25)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 15, 1 top-10", "2025: DNF, 1 top-10", "2024: GC 23"], "Tour de France Femmes": ["2025: DNF"], "Vuelta Espa\u00f1a Femenina": ["2026: GC 7, 2 top-10s", "2025: GC 7, 3 top-10s", "2024: GC 26"]}`

### Morgane Coston (id 31)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| morgane-coston | https://www.procyclingstats.com/rider/morgane-coston | https://www.procyclingstats.com/images/riders/vg/dq/morgane-coston-2026.jpeg | France | 28th December 1990 | 1.62 | 47.0 | 2026-07-19 15:29:29.521887 | 2026-07-20 19:11:19.261830 |

- specialties: `{"Climber": 591, "GC": 197, "Hills": 515, "Onedayraces": 310, "Sprint": 18, "TT": 95}`
- best_results: `["2nd Grand Prix Presidente ('25)", "2nd GC Tour de Feminin ('21)", "3rd Alpes Gresivaudan Classic ('23)", "3rd Grand Prix Boquer\u00f3n ('25)", "3rd stage Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('22)", "4th GC AG Tour de la Semois ('23)", "2nd stage Tour de Feminin ('21)", "2x 8th GC Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('24, '22)", "6th stage Vuelta a Burgos Feminas ('23)", "9th Trofeo Oro in Euro ('23)", "10th La P\u00e9rigord Ladies ('25)", "10th GC Tour Cycliste F\u00e9minin International de l'Ard\u00e8che ('22)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2024: GC 83"], "Tour de France Femmes": ["2025: GC 46", "2023: GC 74", "2022: GC 45"]}`

### Niamh Fisher-Black (id 8)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| niamh-fisher-black | https://www.procyclingstats.com/rider/niamh-fisher-black | https://www.procyclingstats.com/images/riders/my/dq/niamh-fisher-black-2026.jpg | New Zealand | 12th August 2000 | 1.6 |  | 2026-07-19 15:08:34.533083 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 1806, "GC": 1983, "Hills": 1766, "Onedayraces": 1578, "Sprint": 134, "TT": 102}`
- best_results: `["2nd World Championships WE - Road Race ('25)", "stage Giro d'Italia Women ('24)", "stage Tour de Suisse Women ('23)", "stage Setmana Ciclista Valenciana - Vuelta Comunitat V ('24)", "2nd Giro dell'Emilia Internazionale Donne Elite ('25)", "2x 2nd stage Giro d'Italia Internazionale Femminile ('26, '20)", "National Championships New Zealand WE - Road Race ('20)", "3rd GC Setmana Ciclista Valenciana - Vuelta Comunitat V ('24)", "Gravel and Tar la Femme ('20)", "4th GC Tour de Romandie F\u00e9minin ('24)", "2x 5th GC Giro d'Italia Donne ('26, '22)", "4th GC Tour de Suisse Women ('25)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 5, 3 top-10s", "2024: GC 10, 1 stage win, 2 top-10s", "2023: GC 9, 3 top-10s", "2022: GC 5, 4 top-10s", "2021: GC 9, 1 top-10", "2020: GC 21, 1 top-10"], "Tour de France Femmes": ["2025: GC 5, 3 top-10s", "2024: GC 14, 2 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2025: GC 6, 1 top-10", "2024: GC 7, 2 top-10s", "2023: GC 20", "2022: GC 18", "2021: DNF"]}`

### Noémie Abgrall (id 28)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| noemie-abgrall | https://www.procyclingstats.com/rider/noemie-abgrall | https://www.procyclingstats.com/images/riders/cx/dq/noemie-abgrall-2026-n2-n3.jpeg | France | 1st December 1999 | 1.69 |  | 2026-07-19 15:29:29.311321 | 2026-07-20 19:10:19.365285 |

- specialties: `{"Climber": 104, "GC": 37, "Hills": 327, "Onedayraces": 124, "Sprint": 18, "TT": 8}`
- best_results: `["3rd National Championships France WE - Road Race ('22)", "8th GC Tour de Normandie F\u00e9minin ('23)", "8th La P\u00e9rigord Ladies ('26)", "4th Tour du Haut Limousin F\u00e9minin ('26)", "10th Navarra Women's Elite Classics ('22)", "5th R\u00e9gion Pays de la Loire Tour - F\u00e9minin ('25)", "16th Vuelta CV Feminas ('26)", "14th Pionera Race ('26)", "15th Alpes Gresivaudan Classic ('25)", "17th GC Vuelta Ciclista Andalucia Ruta Del Sol ('22)", "2nd KOM Vuelta Extremadura F\u00e9minas ('24)", "26th Classic Lorient Agglom\u00e9ration ('20)"]`
- grand_tour_results: `{"Tour de France Femmes": ["2022: DNF"], "Vuelta Espa\u00f1a Femenina": ["2024: GC 71"]}`

### Océane Mahé (id 34)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oceane-mahe | https://www.procyclingstats.com/rider/oceane-mahe | https://www.procyclingstats.com/images/riders/vg/dq/oceane-mahe-2026.jpeg | France | 12th February 2002 | 1.64 | 52.0 | 2026-07-19 15:29:29.717997 | 2026-07-20 19:13:14.215457 |

- specialties: `{"Climber": 130, "GC": 63, "Hills": 394, "Onedayraces": 76, "Sprint": 39, "TT": 136}`
- best_results: `["Tour du Haut Limousin F\u00e9minin ('26)", "2nd stage Volta a Portugal Feminina ('25)", "11th GC Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('26)", "5th GC Vuelta Extremadura F\u00e9minas ('24)", "5th GC Volta a Portugal Feminina ('24)", "8th Alpes Gresivaudan Classic ('26)", "6th GC Volta a Portugal Feminina ('25)", "3rd stage Vuelta Extremadura F\u00e9minas ('24)", "11th Pionera Race ('26)", "13th Durango - Durango Emakumeen Saria ('24)", "15th Chrono des Nations ('24)", "16th Grand Prix F\u00e9minin de Chamb\u00e9ry ('26)"]`
- grand_tour_results: `{}`

### Paula Blasi (id 22)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| paula-blasi | https://www.procyclingstats.com/rider/paula-blasi | https://www.procyclingstats.com/images/riders/td/dq/paula-blasi-2026.jpeg | Spain | 19th February 2003 | 1.71 | 57.0 | 2026-07-19 15:29:28.823454 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 598, "GC": 866, "Hills": 889, "Onedayraces": 927, "Sprint": 136, "TT": 234}`
- best_results: `["GC Vuelta Espa\u00f1a Femenina ('26)", "Amstel Gold Race Ladies Edition ('26)", "GC Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('26)", "GC Volta Ciclista a Catalunya Femenina ('26)", "Durango - Durango Emakumeen Saria ('26)", "La P\u00e9rigord Ladies ('25)", "Pointe du Raz Ladies Classic ('25)", "Gran Premio Della Liberazione Donne ('25)", "stage Tour de Romandie F\u00e9minin ('25)", "stage Tour F\u00e9minin International des Pyr\u00e9n\u00e9es ('26)", "stage Volta Ciclista a Catalunya Femenina ('26)", "3rd GC Santos Women's Tour Down Under ('26)"]`
- grand_tour_results: `{"Vuelta Espa\u00f1a Femenina": ["2026: GC 1, 3 top-10s"]}`

### Pauline Ferrand-Prévot (id 4)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pauline-ferrand-prevot | https://www.procyclingstats.com/rider/pauline-ferrand-prevot | https://www.procyclingstats.com/images/riders/vg/dq/pauline-ferrand-prevot-2026.jpg | France | 10th February 1992 | 1.65 | 53.0 | 2026-07-19 15:08:34.503022 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 889, "GC": 663, "Hills": 1373, "Onedayraces": 3865, "Sprint": 190, "TT": 832}`
- best_results: `["World Championships WE - Road Race ('14)", "GC Tour de France Femmes ('25)", "Paris-Roubaix Femmes ('25)", "La Fl\u00e8che Wallonne F\u00e9minine ('14)", "2x stage Tour de France Femmes ('25)", "GC WWT Emakumeen Bira ('14)", "2x 2nd Ronde van Vlaanderen WE ('26, '25)", "2nd Trofeo Alfredo Binda - Comune di Cittiglio ('15)", "2nd Classic Lorient Agglom\u00e9ration ('17)", "2x stage WWT Emakumeen Bira ('14)", "stage Giro d'Italia Internazionale Femminile ('15)", "2nd GC Giro d'Italia Internazionale Femminile ('14)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2015: GC 6, 1 stage win, 5 top-10s", "2014: GC 2, 9 top-10s", "2013: GC 28, 2 top-10s"], "Tour de France Femmes": ["2025: GC 1, 2 stage wins, 6 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2026: GC 35, 1 top-10", "2025: DNF"]}`

### Puck Pieterse (id 6)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| puck-pieterse | https://www.procyclingstats.com/rider/puck-pieterse | https://www.procyclingstats.com/images/riders/nk/dq/puck-pieterse-2026-n2-n3.jpg | Netherlands | 13th May 2002 | 1.69 |  | 2026-07-19 15:08:34.518114 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 526, "GC": 72, "Hills": 1222, "Onedayraces": 2448, "Sprint": 226, "TT": 6}`
- best_results: `["La Fl\u00e8che Wallonne F\u00e9minine ('25)", "2x 2nd Li\u00e8ge-Bastogne-Li\u00e8ge Femmes ('26, '25)", "stage Tour de France Femmes ('24)", "2nd La Fl\u00e8che Wallonne F\u00e9minine ('26)", "3rd Ronde van Vlaanderen WE ('26)", "3rd Amstel Gold Race Ladies Edition ('25)", "3rd Trofeo Alfredo Binda - Comune di Cittiglio ('24)", "2nd Trofeo Oro in Euro ('25)", "3rd Ronde van Drenthe ('24)", "4th Milano-Sanremo Donne ('26)", "4th Omloop Het Nieuwsblad WE ('25)", "5th Strade Bianche Donne ('23)"]`
- grand_tour_results: `{"Tour de France Femmes": ["2025: GC 24, 3 top-10s", "2024: GC 11, 1 stage win, 4 top-10s"]}`

### Rachele Barbieri (id 10)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rachele-barbieri | https://www.procyclingstats.com/rider/rachele-barbieri | https://www.procyclingstats.com/images/riders/dw/dq/rachele-barbieri-2026.jpg | Italy | 21st February 1997 | 1.67 | 55.0 | 2026-07-19 15:08:34.548988 | 2026-07-20 19:10:46.413980 |

- specialties: `{"Climber": 0, "GC": 220, "Hills": 93, "Onedayraces": 695, "Sprint": 1297, "TT": 267}`
- best_results: `["stage EasyToys Bloeizone Frysl\u00e2n Tour ('22)", "Omloop der Kempen ('22)", "2nd GP Schellebelle ('22)", "2nd stage Giro d'Italia Donne ('22)", "3rd European Continental Championships WE - Road Race ('22)", "2nd stage UAE Tour Women ('24)", "3rd Schwalbe Women's One Day Classic ('25)", "3rd Scheldeprijs WE ('22)", "3rd Veenendaal - Veenendaal Classic ('22)", "3rd Drentse Acht van Westerveld ('24)", "2nd stage Baloise Ladies Tour ('21)", "2nd National Championships Italy WE - Road Race ('22)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 96", "2023: GC 95, 2 top-10s", "2022: GC 39, 4 top-10s"], "Tour de France Femmes": ["2025: GC 104, 1 top-10", "2024: GC 99, 1 top-10", "2023: DNF", "2022: DNF, 4 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2024: GC 92", "2023: DNF, 1 top-10", "2017: GC 89", "2016: DNF"]}`

### Silvia Persico (id 23)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| silvia-persico | https://www.procyclingstats.com/rider/silvia-persico | https://www.procyclingstats.com/images/riders/td/dq/silvia-persico-2026.jpeg | Italy | 25th July 1997 | 1.64 | 53.0 | 2026-07-19 15:29:29.008893 | 2026-07-20 19:14:52.538334 |

- specialties: `{"Climber": 829, "GC": 1673, "Hills": 2548, "Onedayraces": 2807, "Sprint": 650, "TT": 246}`
- best_results: `["De Brabantse Pijl - La Fl\u00e8che Braban\u00e7onne WE ('23)", "Giro dell'Appennino Donne ('26)", "stage Vuelta Espa\u00f1a Femenina ('22)", "Grand Prix du Morbihan F\u00e9minin ('24)", "Giro del Veneto - Women ('25)", "2nd GC UAE Tour Women ('25)", "3rd World Championships WE - Road Race ('22)", "2nd Tre Valli Varesine Women's Race ('24)", "3rd GC UAE Tour Women ('23)", "2nd Kreiz Breizh Elites F\u00e9minin ('22)", "2nd Trofeo Binissalem-Andratx ('25)", "Gran Premio Della Liberazione Donne ('22)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2026: GC 32, 1 top-10", "2025: GC 28, 1 top-10", "2024: GC 36", "2023: GC 8, 5 top-10s", "2022: GC 7, 5 top-10s", "2018: GC 113", "2017: GC 93"], "Tour de France Femmes": ["2024: GC 69", "2023: GC 14, 1 top-10", "2022: GC 5, 6 top-10s"], "Vuelta Espa\u00f1a Femenina": ["2023: GC 12, 2 top-10s", "2022: GC 12, 1 stage win, 3 top-10s", "2018: GC 82"]}`

### Victoire Berteau (id 25)
| pcs_slug | pcs_url | photo_url | nationality | date_of_birth | height_m | weight_kg | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| victoire-berteau | https://www.procyclingstats.com/rider/victoire-berteau | https://www.procyclingstats.com/images/riders/hh/dq/victoire-berteau-2026.jpg | France | 16th August 2000 | 1.65 | 57.0 | 2026-07-19 15:29:29.140715 | 2026-07-20 19:10:59.065535 |

- specialties: `{"Climber": 2, "GC": 220, "Hills": 699, "Onedayraces": 967, "Sprint": 387, "TT": 291}`
- best_results: `["GC Volta a Portugal Feminina ('26)", "National Championships France WE - Road Race ('23)", "2nd Grand Prix International d'Isbergues ('24)", "2nd Grand Prix du Morbihan F\u00e9minin ('24)", "3rd Grand Prix de Wallonie ('23)", "3rd Grote Prijs Beerens ('24)", "5th Ronde van Drenthe ('24)", "2nd stage Tour de Normandie F\u00e9minin ('24)", "4th GC Tour de Normandie F\u00e9minin ('24)", "2x 5th Grand Prix du Morbihan F\u00e9minin ('25, '23)", "8th Paris-Roubaix Femmes ('24)", "5th La Classique Morbihan ('24)"]`
- grand_tour_results: `{"Giro d'Italia Women": ["2022: GC 68"], "Tour de France Femmes": ["2025: GC 69", "2024: GC 66", "2022: GC 68"]}`

## Event entries
| id | username | event_name | joined_at | status |
| --- | --- | --- | --- | --- |
| 1 | demo | Demo Tour Femmes | 2026-07-19 15:08:34.572902 | active |
| 2 | marianne | Demo Tour Femmes | 2026-07-19 15:08:34.572902 | active |

## Team selections
| id | username | event_name | submitted_at | total_price | rider_count |
| --- | --- | --- | --- | --- | --- |
| 1 | demo | Demo Tour Femmes | 2026-07-20 19:43:37.442012 | 65 | 11 |

Selection 1 riders:
| rider_name | team_name | price |
| --- | --- | --- |
| Demi Vollering | FDJ United - SUEZ (WTW) | 11 |
| Elisa Longo Borghini | UAE Team ADQ (WTW) | 8 |
| Elisa Balsamo | Lidl - Trek (WTW) | 7 |
| Marianne Vos | Team Visma \| Lease a Bike (WTW) | 7 |
| Puck Pieterse | Fenix-Premier Tech (WTW) | 7 |
| Niamh Fisher-Black | Lidl - Trek (WTW) | 6 |
| Cédrine Kerbaol | EF Education-Oatly (WTW) | 5 |
| Maeva Squiban | UAE Team ADQ (WTW) | 5 |
| Liane Lippert | Movistar Team (WTW) | 4 |
| Rachele Barbieri | Team Picnic PostNL (WTW) | 3 |
| Célia Le Mouël | Ma Petite Entreprise (PRW) | 2 |

## Stage lineups
| id | username | event_name | stage_number | stage_name | captain_name | captain_event_rider_id | submitted_at | rider_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | demo | Demo Tour Femmes | 1 | Lausanne › Lausanne | Marianne Vos | 3 | 2026-07-20 19:55:05.498394 | 6 |

Lineup 1 riders:
| rider_name | team_name | price | captain |
| --- | --- | --- | --- |
| Marianne Vos | Team Visma \| Lease a Bike (WTW) | 7 | yes |
| Niamh Fisher-Black | Lidl - Trek (WTW) | 6 |  |
| Cédrine Kerbaol | EF Education-Oatly (WTW) | 5 |  |
| Maeva Squiban | UAE Team ADQ (WTW) | 5 |  |
| Liane Lippert | Movistar Team (WTW) | 4 |  |
| Rachele Barbieri | Team Picnic PostNL (WTW) | 3 |  |

## Stage results
| id | stage_id | event_rider_id | rank | status | time_gap | base_points | imported_at | raw_result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## User stage scores
| id | username | stage_id | score | captain_bonus | calculated_at |
| --- | --- | --- | --- | --- | --- |
| 1 | demo | 1 | 0 | 0 | 2026-07-20 19:55:20.848512 |

## Awards
| id | event_id | stage_id | user_id | award_type | awarded_at |
| --- | --- | --- | --- | --- | --- |

## Live updates
| id | stage_id | posted_at | text | source_url |
| --- | --- | --- | --- | --- |
