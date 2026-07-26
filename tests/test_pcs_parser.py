from datetime import date

from bs4 import BeautifulSoup

from tour_femmes.services.pcs import (
    PcsClient,
    build_live_embed_html,
    minimal_parsed_stage,
    parse_date,
    parse_grand_tour_results,
    parse_label_values,
    parse_classification_results,
    parse_rider_in_race_results,
    parse_specialties,
    parse_stage_name,
    parse_startlist,
    parse_team_image_url,
    parse_top_results,
    retry_after_seconds,
)


def test_parse_startlist_groups_riders_under_current_team():
    html = """
    <main>
      <h2>Preliminary startlist</h2>
      <a href="team/fdj-suez-2026">FDJ United - SUEZ (WTW)</a>
      <a href="rider/demi-vollering">Demi Vollering</a>
      <a href="rider/cedrine-kerbaol">Cedrine Kerbaol</a>
      <a href="team/visma-lease-a-bike-2026">Team Visma | Lease a Bike (WTW)</a>
      <a href="rider/marianne-vos">Marianne Vos</a>
      <p>Do you know teams?</p>
      <a href="rider/not-from-startlist">Ignore Me</a>
    </main>
    """
    soup = BeautifulSoup(html, "html.parser")

    riders = parse_startlist(soup, "https://www.procyclingstats.com")

    assert [rider.name for rider in riders] == ["Demi Vollering", "Cedrine Kerbaol", "Marianne Vos"]
    assert riders[0].team_name == "FDJ United - SUEZ (WTW)"
    assert riders[0].team_url == "https://www.procyclingstats.com/team/fdj-suez-2026"
    assert riders[2].team_name == "Team Visma | Lease a Bike (WTW)"
    assert riders[2].team_url == "https://www.procyclingstats.com/team/visma-lease-a-bike-2026"


def test_parse_classification_results_matches_ranked_riders_to_event_links():
    soup = BeautifulSoup(
        """
        <table>
          <tr><th>Rnk.</th><th>Rider</th><th>Points</th></tr>
          <tr><td>1</td><td><a href="/rider/demi-vollering">Demi Vollering</a></td><td>200</td></tr>
          <tr><td>2</td><td><a href="/rider/marianne-vos">Marianne Vos</a></td><td>180</td></tr>
        </table>
        """,
        "html.parser",
    )

    assert parse_classification_results(
        soup,
        {"demi-vollering": 11, "marianne-vos": 22},
    ) == [(11, 1), (22, 2)]


def test_parse_stage_name_prefers_route_over_results_title():
    text = """
    Tour de France Femmes avec Zwift 2026 Stage 1 results
    Stage 1 | Lausanne-Lausanne
    Results
    2026 | Stage 1
    Lausanne \u203a Lausanne
    (137km)
    """

    assert parse_stage_name(text, 1) == "Lausanne \u203a Lausanne"


def test_parse_stage_name_handles_itt_nav_label():
    text = """
    Tour de France Femmes avec Zwift 2026 Stage 4 (ITT) results
    Stage 4 (ITT) | Gevrey-Chambertin-Dijon
    Results
    """

    assert parse_stage_name(text, 4) == "Gevrey-Chambertin-Dijon"


def test_live_embed_keeps_livestats_and_removes_unsafe_page_content():
    soup = BeautifulSoup(
        """
        <html>
          <head><link rel="stylesheet" href="v3_site.css"></head>
          <body>
            <div class="page-content">
              <div>
                <ul class="ls5b-kpi"><li><span>KM to go</span><div>138.6</div></li></ul>
                <div class="ls5b-left">
                  <form><input name="request"></form>
                  <img src="/images/riders/example.jpg">
                  <ul class="timeline3">
                    <li class="event">A real race update</li>
                    <li class="event">advertisement</li>
                  </ul>
                </div>
                <a href="rider/example" onclick="track()">Example rider</a>
                <script>window.bad = true;</script>
              </div>
            </div>
          </body>
        </html>
        """,
        "html.parser",
    )

    html = build_live_embed_html(
        soup,
        "https://www.procyclingstats.com/race/example/2026/stage-1/live",
    )

    assert "KM to go" in html
    assert "A real race update" in html
    assert "advertisement" not in html
    assert "<script" not in html
    assert "<form" not in html
    assert "onclick" not in html
    assert 'href="https://www.procyclingstats.com/rider/example"' in html
    assert 'src="https://www.procyclingstats.com/images/riders/example.jpg"' in html
    assert 'referrerpolicy="no-referrer"' in html
    assert '<meta http-equiv="refresh" content="30">' in html


def test_parse_stage_race_info_keeps_august_intact():
    text = """
    Race information
    Date:
    01 August 2026
    Start time:
    14:40
    Distance:
    137 km
    ProfileScore:
    63
    """

    values = parse_label_values(text)

    assert values["Date"] == "01 August 2026"
    assert parse_date(values["Date"]) == date(2026, 8, 1)


def test_parse_structured_top_results_and_grand_tours():
    html = """
    <ul class="list topresults">
      <li>
        <div class="nrs">3x</div>
        <div class="races">
          <a href="race/liege-bastogne-liege-femmes/2021/result">Liege-Bastogne-Liege Femmes</a>
          <span class="clr777 fs11">('26, '23, '21)</span>
        </div>
      </li>
      <li>
        <div class="nrs">*</div>
        <div class="races">
          <span class="blue">GC</span>
          <a href="race/tour-de-france-femmes/2023/gc">Tour de France Femmes</a>
          <span class="clr777 fs11">('23)</span>
        </div>
      </li>
    </ul>
    """
    soup = BeautifulSoup(html, "html.parser")

    top_results = parse_top_results(soup, [])
    grand_tours = parse_grand_tour_results([], top_results)

    assert top_results == [
        "3x Liege-Bastogne-Liege Femmes ('26, '23, '21)",
        "GC Tour de France Femmes ('23)",
    ]
    assert grand_tours == {"Tour de France Femmes": ["GC Tour de France Femmes ('23)"]}


def test_parse_grand_tour_results_maps_historical_womens_race_names():
    top_results = [
        "32x stage Giro d'Italia Femminile ('22, '21, '20, '19, '18, '14, '13, '12, '11, '10, '07)",
        "2x stage Vuelta España Femenina by Carrefour.es ('25, '24)",
    ]

    grand_tours = parse_grand_tour_results([], top_results)

    assert grand_tours == {
        "Giro d'Italia Women": [top_results[0]],
        "Vuelta España Femenina": [top_results[1]],
    }


def test_parse_rider_in_race_results_from_pcs_yearly_table():
    html = """
    <table class="basic">
      <tr>
        <th>Year</th><th>Result</th><th>Stage wins</th><th>Stage top10s</th><th>Stage starts</th>
      </tr>
      <tr><td>2025</td><td>37</td><td>1</td><td>5</td><td>9</td></tr>
      <tr><td>2024</td><td>31</td><td>-</td><td>4</td><td>8</td></tr>
      <tr><td>2023</td><td>DNF</td><td>-</td><td>3</td><td>7</td></tr>
      <tr><td></td><td></td><td>3</td><td>18</td><td>32</td></tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")

    assert parse_rider_in_race_results(soup) == [
        "2025: GC 37, 1 stage win, 5 top-10s",
        "2024: GC 31, 4 top-10s",
        "2023: DNF, 3 top-10s",
    ]


def test_parse_team_image_url_prefers_pcs_shirt_asset():
    html = """
    <main>
      <img src="images/riders/vg/em/marianne-vos-2026.jpg">
      <img src="images/shirts/bx/eb/team-visma-lease-a-bike-women-2026-n2.png">
    </main>
    """
    soup = BeautifulSoup(html, "html.parser")
    client = PcsClient(base_url="https://www.procyclingstats.com")

    assert (
        parse_team_image_url(soup, client)
        == "https://www.procyclingstats.com/images/shirts/bx/eb/team-visma-lease-a-bike-women-2026-n2.png"
    )


def test_retry_after_seconds_uses_retry_after_header():
    response = type("Response", (), {"headers": {"Retry-After": "42"}})()

    assert retry_after_seconds(response, attempt=0, base_backoff=30) == 42


def test_retry_after_seconds_uses_conservative_backoff_without_header():
    response = type("Response", (), {"headers": {}})()

    assert retry_after_seconds(response, attempt=1, base_backoff=30) == 60


def test_minimal_parsed_stage_keeps_stage_sync_idempotent_after_rate_limit():
    parsed = minimal_parsed_stage(2, "https://www.procyclingstats.com/race/example/2026/stage-2")

    assert parsed.number == 2
    assert parsed.name == "Etappe 2"
    assert parsed.live_url.endswith("/stage-2/live")


def test_parse_specialties_uses_highest_score_for_duplicate_labels():
    lines = [
        "7800",
        "Onedayraces",
        "5996",
        "GC",
        "2055",
        "TT",
        "576",
        "Sprint",
        "3388",
        "Climber",
        "5728",
        "Hills",
        "26",
        "GC",
    ]

    assert parse_specialties(lines) == {
        "Onedayraces": 7800,
        "GC": 5996,
        "TT": 2055,
        "Sprint": 576,
        "Climber": 3388,
        "Hills": 5728,
    }
