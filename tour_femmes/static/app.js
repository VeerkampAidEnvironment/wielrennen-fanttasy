(function () {
  function updateTeamForm(form) {
    const maxCount = Number(form.dataset.teamSize || 0);
    const budget = Number(form.dataset.budget || 0);
    const boxes = Array.from(form.querySelectorAll('input[name="riders"]'));
    const checked = boxes.filter((box) => box.checked);
    const total = checked.reduce((sum, box) => sum + Number(box.dataset.price || 0), 0);

    form.querySelectorAll(".rider-card").forEach((card) => {
      const box = card.querySelector('input[name="riders"]');
      card.classList.toggle("selected", Boolean(box && box.checked));
      card.classList.remove("in-selected-team");
      if (box) {
        card.setAttribute("aria-pressed", box.checked ? "true" : "false");
      }
    });

    document.querySelectorAll("[data-count]").forEach((node) => {
      node.textContent = checked.length;
    });
    document.querySelectorAll("[data-budget-total]").forEach((node) => {
      node.textContent = total;
      node.style.color = total > budget ? "var(--danger)" : "";
    });
    updateTeamStatus(checked.length, total, maxCount, budget);
    renderSelectedTeam(form, checked);

    boxes.forEach((box) => {
      const card = box.closest(".rider-card");
      const action = card?.querySelector("[data-selection-action]");
      const price = Number(box.dataset.price || 0);
      const exceedsBudget = !box.checked && total + price > budget;
      if (box.dataset.fixedDisabled === "1") {
        box.disabled = true;
        card?.classList.add("disabled", "fixed-disabled");
        card?.classList.remove("capacity-disabled", "budget-disabled");
        if (action) {
          action.textContent = box.checked ? "Geselecteerd" : card.dataset.unavailableReason || "Niet beschikbaar";
        }
      } else if (!box.checked && checked.length >= maxCount) {
        box.disabled = true;
        card?.classList.add("disabled", "capacity-disabled");
        card?.classList.remove("fixed-disabled", "budget-disabled");
        if (action) {
          action.textContent = "Team vol";
        }
      } else if (exceedsBudget) {
        box.disabled = true;
        card?.classList.add("disabled", "budget-disabled");
        card?.classList.remove("fixed-disabled", "capacity-disabled");
        if (action) {
          action.textContent = "Boven budget";
        }
      } else {
        box.disabled = false;
        card?.classList.remove("disabled", "fixed-disabled", "capacity-disabled", "budget-disabled");
        if (action) {
          action.textContent = box.checked ? "Renner verwijderen" : "Renner toevoegen";
        }
      }
    });
    applyTeamFiltersAndSort(form);
  }

  function renderSelectedTeam(form, checked) {
    const list = form.querySelector("[data-selected-team-list]");
    const empty = form.querySelector("[data-selected-team-empty]");
    if (!list) {
      return;
    }

    list.replaceChildren();
    checked.forEach((box) => {
      const card = box.closest(".rider-card");
      if (!card) {
        return;
      }
      list.appendChild(createSelectedTeamRider(card, box));
    });

    empty?.classList.toggle("hidden", checked.length > 0);
  }

  function createSelectedTeamRider(card, box) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "my-team-rider";
    button.value = box.value;
    button.setAttribute("data-selected-team-rider", "");
    button.disabled = box.dataset.fixedDisabled === "1";

    const photo = document.createElement("span");
    photo.className = "my-team-photo";
    const sourceImage = card.querySelector(".rider-card-media img");
    const sourceInitials = card.querySelector(".rider-initials");
    if (sourceImage) {
      const image = document.createElement("img");
      image.src = sourceImage.currentSrc || sourceImage.src;
      image.alt = "";
      photo.appendChild(image);
    } else {
      const fallback = document.createElement("span");
      fallback.textContent = sourceInitials?.textContent?.trim() || "R";
      photo.appendChild(fallback);
    }

    const main = document.createElement("span");
    main.className = "my-team-main";
    const name = document.createElement("strong");
    name.textContent = card.querySelector(".rider-main strong")?.textContent?.trim() || "Renner";
    button.setAttribute("aria-label", `${name.textContent} uit mijn team verwijderen`);
    button.title = "Verwijder uit mijn team";
    const team = document.createElement("small");
    team.textContent = card.querySelector(".rider-team-line span")?.textContent?.trim() || "Geen ploeg";
    main.append(name, team);

    const price = document.createElement("span");
    price.className = "my-team-price";
    price.textContent = card.dataset.price || "0";

    button.append(photo, main, price);
    return button;
  }

  function updateTeamStatus(count, total, maxCount, budget) {
    const remainingRiders = Math.max(maxCount - count, 0);
    const remainingBudget = budget - total;
    const completionPercent = maxCount ? Math.min(Math.round((count / maxCount) * 100), 100) : 0;
    const budgetPercentRaw = budget ? Math.round((total / budget) * 100) : 0;
    const budgetPercent = Math.max(Math.min(budgetPercentRaw, 100), 0);
    const complete = count === maxCount && total <= budget;
    const overBudget = total > budget;
    updateNavigationSelectionState(
      "[data-team-selection-tab]",
      count,
      maxCount,
      complete,
    );

    document.querySelectorAll("[data-team-status-card]").forEach((card) => {
      card.classList.toggle("complete", complete);
      card.classList.toggle("over-budget", overBudget);
    });
    setStatusText("[data-status-count]", count);
    setStatusText("[data-status-total]", total);
    setStatusText("[data-status-completion]", `${completionPercent}%`);
    setStatusText("[data-status-budget-percent]", `${budgetPercentRaw}%`);
    setStatusText("[data-status-label]", overBudget ? "Boven budget" : complete ? "Compleet" : "Concept");
    setStatusText(
      "[data-status-rider-note]",
      remainingRiders === 0 ? "Selectie vol" : `Nog ${remainingRiders} renner${remainingRiders === 1 ? "" : "s"}`,
    );
    setStatusText(
      "[data-status-budget-note]",
      overBudget ? `${Math.abs(remainingBudget)} boven budget` : `${remainingBudget} over`,
    );
    setStatusWidth("[data-status-complete-bar]", completionPercent);
    setStatusWidth("[data-status-budget-bar]", budgetPercent);
  }

  function setStatusText(selector, value) {
    document.querySelectorAll(selector).forEach((node) => {
      node.textContent = value;
    });
  }

  function setStatusWidth(selector, value) {
    document.querySelectorAll(selector).forEach((node) => {
      node.style.width = `${value}%`;
    });
  }

  function updateNavigationSelectionState(selector, count, required, complete) {
    const state = complete ? "complete" : count > 0 ? "partial" : "empty";
    const label = complete ? "Compleet" : count > 0 ? `${count}/${required}` : "Leeg";

    document.querySelectorAll(selector).forEach((tab) => {
      tab.classList.remove(
        "selection-state-complete",
        "selection-state-partial",
        "selection-state-empty",
        "selection-state-ongoing",
        "selection-state-finished",
      );
      tab.classList.add(`selection-state-${state}`);
      tab.dataset.selectionState = state;
      if (tab.hasAttribute("data-stage-selection-state")) {
        tab.dataset.stageSelectionState = state;
      }
      const status = tab.querySelector(".event-tab-status");
      if (status) {
        status.textContent = label;
      }
      const selectionLabel = tab.dataset.selectionLabel || "Selectie";
      tab.setAttribute("aria-label", `${selectionLabel}, selectie ${label}`);
    });
  }

  function updateStageNavigationLifecycle() {
    const now = Date.now();
    document.querySelectorAll("[data-stage-selection-tab][data-stage-start-at]").forEach((tab) => {
      if (tab.dataset.stageLifecycleState === "finished") {
        return;
      }
      const startsAt = Number(tab.dataset.stageStartAt);
      if (!Number.isFinite(startsAt) || startsAt > now) {
        return;
      }

      tab.classList.remove(
        "selection-state-complete",
        "selection-state-partial",
        "selection-state-empty",
      );
      tab.classList.add("selection-state-ongoing");
      tab.dataset.selectionState = "ongoing";
      tab.dataset.stageSelectionState = "ongoing";
      tab.dataset.stageLifecycleState = "ongoing";
      const status = tab.querySelector(".event-tab-status");
      if (status) {
        status.textContent = "Bezig";
      }
      const selectionLabel = tab.dataset.selectionLabel || "Etappe";
      tab.setAttribute("aria-label", `${selectionLabel}, status Bezig`);
    });
  }

  function applyTeamFiltersAndSort(form) {
    const grid = form.querySelector(".rider-grid");
    if (!grid) {
      return;
    }

    const search = (form.querySelector("[data-rider-search]")?.value || "").trim().toLowerCase();
    const team = form.querySelector("[data-team-filter]")?.value || "";
    const priceRange = syncPriceControls(form);
    const sort = form.querySelector("[data-sort-filter]")?.value || "price-desc";
    const cards = Array.from(grid.querySelectorAll("[data-rider-card]"));

    let visibleCount = 0;
    cards.forEach((card) => {
      const price = Number(card.dataset.price || -1);
      const selected = Boolean(card.querySelector('input[name="riders"]')?.checked);
      const matchesSearch = !search || (card.dataset.riderName || "").includes(search);
      const matchesTeam = !team || card.dataset.team === team;
      const matchesPrice = price >= priceRange.min && price <= priceRange.max;
      const visible = matchesSearch && matchesTeam && matchesPrice;
      card.classList.toggle("filtered-out", !visible);
      if (visible && !selected) {
        visibleCount += 1;
      }
    });

    cards
      .sort((a, b) => compareRiderCards(a, b, sort))
      .forEach((card) => grid.appendChild(card));

    form.querySelectorAll("[data-visible-count]").forEach((node) => {
      node.textContent = visibleCount;
    });
    syncTeamFilterChips(form);
  }

  function compareRiderCards(a, b, sort) {
    const priceA = Number(a.dataset.price || -1);
    const priceB = Number(b.dataset.price || -1);
    const nameA = a.dataset.riderName || "";
    const nameB = b.dataset.riderName || "";
    const pricedA = priceA >= 0;
    const pricedB = priceB >= 0;

    if (pricedA !== pricedB) {
      return pricedA ? -1 : 1;
    }

    if (sort.startsWith("speciality-")) {
      const key = sort.replace("speciality-", "").replace("-desc", "");
      const valueA = Number(a.dataset[`speciality${toDatasetSuffix(key)}`] || 0);
      const valueB = Number(b.dataset[`speciality${toDatasetSuffix(key)}`] || 0);
      if (valueA !== valueB) {
        return valueB - valueA;
      }
      if (priceA !== priceB) {
        return priceB - priceA;
      }
      return nameA.localeCompare(nameB);
    }

    if (sort === "price-asc" && priceA !== priceB) {
      return priceA - priceB;
    }
    if (priceA !== priceB) {
      return priceB - priceA;
    }
    return nameA.localeCompare(nameB);
  }

  function toDatasetSuffix(value) {
    return (value || "")
      .split("-")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join("");
  }

  function resetTeamFilters(form) {
    const search = form.querySelector("[data-rider-search]");
    const team = form.querySelector("[data-team-filter]");
    const sort = form.querySelector("[data-sort-filter]");
    const controls = priceControls(form);
    const bounds = priceBounds(form);
    if (search) {
      search.value = "";
    }
    if (team) {
      team.value = "";
    }
    if (sort) {
      sort.value = "price-desc";
    }
    [controls.minInput, controls.minRange].forEach((control) => {
      if (control) {
        control.value = bounds.min;
      }
    });
    [controls.maxInput, controls.maxRange].forEach((control) => {
      if (control) {
        control.value = bounds.max;
      }
    });
    syncPriceControls(form);
    applyTeamFiltersAndSort(form);
  }

  function syncTeamFilterChips(form) {
    const selectedTeam = form.querySelector("[data-team-filter]")?.value || "";
    form.querySelectorAll("[data-team-chip]").forEach((chip) => {
      chip.classList.toggle("active", chip.value === selectedTeam);
    });
  }

  function priceControls(form) {
    return {
      minInput: form.querySelector("[data-price-min-input]"),
      maxInput: form.querySelector("[data-price-max-input]"),
      minRange: form.querySelector("[data-price-min-range]"),
      maxRange: form.querySelector("[data-price-max-range]"),
      label: form.querySelector("[data-price-range-label]"),
      fill: form.querySelector("[data-price-range-fill]"),
    };
  }

  function priceBounds(form) {
    const min = numberOrFallback(form.dataset.priceMin, 0);
    const max = numberOrFallback(form.dataset.priceMax, min);
    return { min, max: Math.max(min, max) };
  }

  function numberOrFallback(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function syncPriceControls(form, changedControl) {
    const controls = priceControls(form);
    const bounds = priceBounds(form);
    let min = numberOrFallback(controls.minInput?.value, bounds.min);
    let max = numberOrFallback(controls.maxInput?.value, bounds.max);

    if (changedControl === controls.minRange) {
      min = numberOrFallback(controls.minRange.value, bounds.min);
    }
    if (changedControl === controls.maxRange) {
      max = numberOrFallback(controls.maxRange.value, bounds.max);
    }
    if (changedControl === controls.minInput) {
      min = numberOrFallback(controls.minInput.value, bounds.min);
    }
    if (changedControl === controls.maxInput) {
      max = numberOrFallback(controls.maxInput.value, bounds.max);
    }

    min = clamp(min, bounds.min, bounds.max);
    max = clamp(max, bounds.min, bounds.max);
    if (min > max) {
      if (changedControl === controls.maxInput || changedControl === controls.maxRange) {
        min = max;
      } else {
        max = min;
      }
    }

    [controls.minInput, controls.minRange].forEach((control) => {
      if (control) {
        control.value = min;
      }
    });
    [controls.maxInput, controls.maxRange].forEach((control) => {
      if (control) {
        control.value = max;
      }
    });
    if (controls.label) {
      controls.label.textContent = `${min} - ${max}`;
    }
    if (controls.fill) {
      const span = Math.max(bounds.max - bounds.min, 1);
      const start = ((min - bounds.min) / span) * 100;
      const end = ((max - bounds.min) / span) * 100;
      controls.fill.style.left = `${start}%`;
      controls.fill.style.right = `${100 - end}%`;
    }
    return { min, max };
  }

  function preserveScroll(action) {
    const x = window.scrollX;
    const y = window.scrollY;
    action();
    window.requestAnimationFrame(() => {
      window.scrollTo(x, y);
    });
  }

  function selectedTeamRiderIds(form) {
    return Array.from(form.querySelectorAll('input[name="riders"]'))
      .filter((box) => box.checked)
      .map((box) => box.value);
  }

  function setAutosaveStatus(form, text, state, autoClear) {
    const status = form.querySelector("[data-autosave-status]") || document.querySelector("[data-autosave-status]");
    if (!status) {
      return;
    }
    window.clearTimeout(form._autosaveStatusTimer);
    status.textContent = text || "";
    status.dataset.state = state || "";
    if (autoClear) {
      form._autosaveStatusTimer = window.setTimeout(() => {
        status.textContent = "";
        status.dataset.state = "";
      }, 2200);
    }
  }

  function setTeamAutosaveStatus(form, text, state, autoClear) {
    setAutosaveStatus(form, text, state, autoClear);
  }

  function scheduleTeamAutosave(form) {
    window.clearTimeout(form._autosaveTimer);
    form._autosaveTimer = window.setTimeout(() => saveTeamSelection(form), 350);
  }

  function syncTeamSelection(form) {
    preserveScroll(() => updateTeamForm(form));
    scheduleTeamAutosave(form);
  }

  function toggleTeamRiderCard(card, form) {
    const box = card.querySelector('input[name="riders"]');
    if (!box || box.dataset.fixedDisabled === "1" || (box.disabled && !box.checked)) {
      return;
    }
    const budget = Number(form.dataset.budget || 0);
    const currentTotal = Array.from(form.querySelectorAll('input[name="riders"]'))
      .filter((candidate) => candidate.checked)
      .reduce((sum, candidate) => sum + Number(candidate.dataset.price || 0), 0);
    const price = Number(box.dataset.price || 0);
    if (!box.checked && currentTotal + price > budget) {
      updateTeamForm(form);
      return;
    }
    preserveScroll(() => {
      box.checked = !box.checked;
      updateTeamForm(form);
    });
    scheduleTeamAutosave(form);
  }

  function toggleRiderDetails(card, form) {
    const expanded = !card.classList.contains("expanded");
    if (expanded) {
      form.querySelectorAll("[data-rider-card].expanded").forEach((otherCard) => {
        if (otherCard !== card) {
          setRiderDetails(otherCard, false);
        }
      });
    }
    setRiderDetails(card, expanded);
  }

  function setRiderDetails(card, expanded) {
    const button = card.querySelector("[data-card-toggle]");
    card.classList.toggle("expanded", expanded);
    if (button) {
      button.setAttribute("aria-expanded", expanded ? "true" : "false");
      button.textContent = expanded ? "Minder details" : "Details";
    }
  }

  function toggleLineupRiderProfile(card, form) {
    const expanded = !card.classList.contains("profile-expanded");
    if (expanded) {
      form.querySelectorAll("[data-lineup-card].profile-expanded").forEach((otherCard) => {
        if (otherCard !== card) {
          setLineupRiderProfile(otherCard, false);
        }
      });
    }
    setLineupRiderProfile(card, expanded);
  }

  function setLineupRiderProfile(card, expanded) {
    const button = card.querySelector("[data-toggle-lineup-profile]");
    card.classList.toggle("profile-expanded", expanded);
    if (button) {
      button.setAttribute("aria-expanded", expanded ? "true" : "false");
      button.textContent = expanded ? "Sluiten" : "Profiel";
    }
  }

  async function saveTeamSelection(form) {
    const csrf = form.querySelector('input[name="csrf_token"]')?.value || "";
    const body = new URLSearchParams();
    body.set("csrf_token", csrf);
    selectedTeamRiderIds(form).forEach((id) => body.append("riders", id));

    const sequence = (form._autosaveSequence || 0) + 1;
    form._autosaveSequence = sequence;
    setTeamAutosaveStatus(form, "Opslaan", "saving", false);

    try {
      const response = await fetch(form.action || window.location.href, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "fetch",
        },
        body,
      });
      const payload = await response.json();
      if (sequence !== form._autosaveSequence) {
        return;
      }
      if (!response.ok || !payload.ok) {
        throw new Error(payload.message || "Opslaan mislukt");
      }
      if (typeof payload.count === "number") {
        document.querySelectorAll("[data-count]").forEach((node) => {
          node.textContent = payload.count;
        });
      }
      if (typeof payload.total_price === "number") {
        document.querySelectorAll("[data-budget-total]").forEach((node) => {
          node.textContent = payload.total_price;
        });
      }
      setTeamAutosaveStatus(form, payload.complete ? "Team opgeslagen" : "Concept opgeslagen", "saved", true);
    } catch (error) {
      if (sequence !== form._autosaveSequence) {
        return;
      }
      setTeamAutosaveStatus(form, error.message || "Opslaan mislukt", "error", false);
    }
  }

  function renderEmptyLineupSlots(selectedZone, openCount) {
    if (!selectedZone) {
      return;
    }
    selectedZone.querySelectorAll("[data-empty-slot]").forEach((slot) => slot.remove());
    for (let index = 0; index < openCount; index += 1) {
      const slot = document.createElement("div");
      slot.className = "lineup-empty-slot";
      slot.setAttribute("data-empty-slot", "");
      slot.textContent = "Open plek";
      selectedZone.appendChild(slot);
    }
  }

  function selectedLineupRiderIds(form) {
    return Array.from(form.querySelectorAll("[data-lineup-checkbox]"))
      .filter((box) => box.checked)
      .map((box) => box.value);
  }

  function scheduleLineupAutosave(form) {
    window.clearTimeout(form._lineupAutosaveTimer);
    form._lineupAutosaveTimer = window.setTimeout(() => saveStageLineup(form), 350);
  }

  function syncLineupSelection(form) {
    preserveScroll(() => updateLineupForm(form));
    scheduleLineupAutosave(form);
  }

  function updateLineupForm(form) {
    const maxCount = Number(form.dataset.teamSize || 0);
    const selectedZone = form.querySelector("[data-selected-lineup]");
    const benchZone = form.querySelector("[data-bench-lineup]");
    const boxes = Array.from(form.querySelectorAll("[data-lineup-checkbox]"));
    const checked = boxes.filter((box) => box.checked);
    const checkedIds = new Set(checked.map((box) => box.value));
    let captain = form.querySelector("[data-captain-radio]:checked");

    if (captain && !checkedIds.has(captain.value)) {
      captain.checked = false;
      captain = null;
    }
    if (!captain && checked.length > 0) {
      const firstCaptain = checked[0].closest("[data-lineup-card]")?.querySelector("[data-captain-radio]");
      if (firstCaptain && firstCaptain.dataset.fixedDisabled !== "1") {
        firstCaptain.checked = true;
        captain = firstCaptain;
      }
    }

    const stageId = form.dataset.stageId || "";
    if (stageId) {
      updateNavigationSelectionState(
        `[data-stage-selection-tab="${stageId}"]`,
        checked.length,
        maxCount,
        checked.length === maxCount && Boolean(captain),
      );
    }

    form.querySelectorAll("[data-count]").forEach((count) => {
      count.textContent = checked.length;
    });

    renderEmptyLineupSlots(selectedZone, 0);

    boxes.forEach((box) => {
      const card = box.closest("[data-lineup-card]");
      const radio = card?.querySelector("[data-captain-radio]");
      const toggle = card?.querySelector("[data-toggle-lineup]");
      const captainButton = card?.querySelector("[data-toggle-captain]");
      const selected = box.checked;

      if (box.dataset.fixedDisabled === "1") {
        box.disabled = true;
      } else if (!selected && checked.length >= maxCount) {
        box.disabled = true;
      } else {
        box.disabled = false;
      }

      if (radio) {
        radio.disabled = radio.dataset.fixedDisabled === "1" || !selected;
      }
      if (card) {
        card.classList.toggle("selected", selected);
        card.classList.toggle("captain", Boolean(radio && radio.checked && selected));
        card.classList.toggle("capacity-disabled", !selected && checked.length >= maxCount);
        card.setAttribute("aria-pressed", selected ? "true" : "false");
        if (selectedZone && benchZone) {
          if (selected) {
            selectedZone.appendChild(card);
          } else {
            benchZone.appendChild(card);
          }
        }
      }
      if (toggle) {
        toggle.disabled = box.disabled && !selected;
        if (selected) {
          toggle.textContent = "Verwijderen";
        } else if (box.disabled) {
          toggle.textContent = "Selectie vol";
        } else {
          toggle.textContent = "Toevoegen";
        }
      }
      if (captainButton) {
        captainButton.disabled = !selected || Boolean(radio && radio.disabled);
        captainButton.textContent = radio && radio.checked && selected ? "Kopvrouw gekozen" : "Kopvrouw";
      }
    });

    renderEmptyLineupSlots(selectedZone, Math.max(maxCount - checked.length, 0));

    const captainMeter = form.querySelector("[data-captain-meter]");
    if (captainMeter) {
      if (captain && checkedIds.has(captain.value)) {
        const captainCard = captain.closest("[data-lineup-card]");
        const captainName = captainCard?.querySelector(".lineup-card-main strong")?.textContent || "Kopvrouw gekozen";
        captainMeter.textContent = captainName;
      } else {
        captainMeter.textContent = "Geen kopvrouw";
      }
    }
  }

  function toggleLineupCard(card, form) {
    const box = card.querySelector("[data-lineup-checkbox]");
    if (!box || box.dataset.fixedDisabled === "1" || (box.disabled && !box.checked)) {
      return;
    }
    preserveScroll(() => {
      box.checked = !box.checked;
      updateLineupForm(form);
    });
    scheduleLineupAutosave(form);
  }

  function setCaptain(card, form) {
    const box = card.querySelector("[data-lineup-checkbox]");
    const radio = card.querySelector("[data-captain-radio]");
    if (!box || !radio || box.dataset.fixedDisabled === "1" || !box.checked || radio.disabled) {
      return;
    }
    preserveScroll(() => {
      radio.checked = true;
      updateLineupForm(form);
    });
    scheduleLineupAutosave(form);
  }

  async function saveStageLineup(form) {
    const csrf = form.querySelector('input[name="csrf_token"]')?.value || "";
    const body = new URLSearchParams();
    const captain = form.querySelector("[data-captain-radio]:checked");

    body.set("csrf_token", csrf);
    selectedLineupRiderIds(form).forEach((id) => body.append("riders", id));
    if (captain) {
      body.set("captain", captain.value);
    }

    const sequence = (form._lineupAutosaveSequence || 0) + 1;
    form._lineupAutosaveSequence = sequence;
    setAutosaveStatus(form, "Opslaan", "saving", false);

    try {
      const response = await fetch(form.action || window.location.href, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "fetch",
        },
        body,
      });
      let payload = {};
      try {
        payload = await response.json();
      } catch (_error) {
        throw new Error("Opslaan mislukt");
      }
      if (sequence !== form._lineupAutosaveSequence) {
        return;
      }
      if (!response.ok || !payload.ok) {
        throw new Error(payload.message || "Opslaan mislukt");
      }
      if (typeof payload.count === "number") {
        form.querySelectorAll("[data-count]").forEach((node) => {
          node.textContent = payload.count;
        });
      }
      setAutosaveStatus(
        form,
        payload.complete ? "Etappeselectie opgeslagen" : "Concept opgeslagen",
        "saved",
        true,
      );
    } catch (error) {
      if (sequence !== form._lineupAutosaveSequence) {
        return;
      }
      setAutosaveStatus(form, error.message || "Opslaan mislukt", "error", false);
    }
  }

  function adminJobPanel() {
    return {
      panel: document.querySelector("[data-admin-job-panel]"),
      title: document.querySelector("[data-admin-job-title]"),
      label: document.querySelector("[data-admin-job-label]"),
      count: document.querySelector("[data-admin-job-count]"),
      progress: document.querySelector("[data-admin-job-progress]"),
      bar: document.querySelector("[data-admin-job-bar]"),
      message: document.querySelector("[data-admin-job-message]"),
      refresh: document.querySelector("[data-admin-job-refresh]"),
    };
  }

  function setAdminJobFormsDisabled(disabled) {
    document.querySelectorAll("[data-admin-job-form]").forEach((form) => {
      form.querySelectorAll("button, input").forEach((control) => {
        control.disabled = disabled;
      });
    });
  }

  function updateAdminJobPanel(payload) {
    const nodes = adminJobPanel();
    if (!nodes.panel) {
      return;
    }
    const current = Number(payload.current || 0);
    const total = Number(payload.total || 0);
    const complete = payload.status === "done";
    const ok = payload.ok !== false;
    const percent = total ? Math.min(Math.round((current / total) * 100), 100) : 0;

    nodes.panel.classList.remove("hidden", "done", "error");
    nodes.panel.classList.toggle("done", complete && ok);
    nodes.panel.classList.toggle("error", complete && !ok);
    nodes.title.textContent = payload.title || "PCS laden";
    nodes.label.textContent = payload.label || "PCS";
    nodes.count.textContent = total ? `${current} / ${total}` : `${current}`;
    nodes.message.textContent = payload.message || "";
    nodes.progress.classList.toggle("indeterminate", !complete && total === 0);
    nodes.bar.style.width = total ? `${percent}%` : "";

    if (nodes.refresh) {
      nodes.refresh.classList.toggle("hidden", !complete);
      nodes.refresh.onclick = () => {
        window.location.href = payload.redirect_url || window.location.href;
      };
    }
  }

  async function startAdminJob(form) {
    const title = form.dataset.jobTitle || "PCS laden";
    const body = new FormData(form);
    setAdminJobFormsDisabled(true);
    updateAdminJobPanel({
      title,
      status: "queued",
      current: 0,
      total: 0,
      label: "PCS",
      message: "Job starten...",
      ok: null,
    });

    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "fetch",
        },
        body,
      });
      const payload = await response.json();
      if (!response.ok || !payload.id) {
        throw new Error(payload.message || "Job starten mislukt");
      }
      updateAdminJobPanel(payload);
      pollAdminJob(`/admin/jobs/${payload.id}`);
    } catch (error) {
      setAdminJobFormsDisabled(false);
      updateAdminJobPanel({
        title,
        status: "done",
        current: 0,
        total: 0,
        label: "Fout",
        message: error.message || "Job starten mislukt",
        ok: false,
      });
    }
  }

  async function pollAdminJob(url) {
    try {
      const response = await fetch(url, {
        headers: {
          Accept: "application/json",
          "X-Requested-With": "fetch",
        },
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.message || "Voortgang ophalen mislukt");
      }
      updateAdminJobPanel(payload);
      if (payload.status !== "done") {
        window.setTimeout(() => pollAdminJob(url), 900);
      } else {
        setAdminJobFormsDisabled(false);
      }
    } catch (error) {
      setAdminJobFormsDisabled(false);
      updateAdminJobPanel({
        title: "PCS laden",
        status: "done",
        current: 0,
        total: 0,
        label: "Fout",
        message: error.message || "Voortgang ophalen mislukt",
        ok: false,
      });
    }
  }

  document.querySelectorAll("[data-team-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      saveTeamSelection(form);
    });
    form.addEventListener("click", (event) => {
      const selectedTeamButton = event.target.closest("[data-selected-team-rider]");
      if (selectedTeamButton) {
        event.preventDefault();
        const box = Array.from(form.querySelectorAll('input[name="riders"]')).find(
          (candidate) => candidate.value === selectedTeamButton.value,
        );
        if (box && box.checked && box.dataset.fixedDisabled !== "1") {
          preserveScroll(() => {
            box.checked = false;
            updateTeamForm(form);
          });
          scheduleTeamAutosave(form);
        }
        return;
      }

      const detailButton = event.target.closest("[data-card-toggle]");
      if (detailButton) {
        event.preventDefault();
        const card = detailButton.closest("[data-rider-card]");
        if (card) {
          preserveScroll(() => toggleRiderDetails(card, form));
        }
        return;
      }

      const card = event.target.closest("[data-rider-card]");
      if (!card || event.target.closest("button, select, input[type='search']")) {
        return;
      }
      event.preventDefault();
      toggleTeamRiderCard(card, form);
    });
    form.addEventListener("change", (event) => {
      if (event.target.matches('input[name="riders"]')) {
        syncTeamSelection(form);
      } else {
        updateTeamForm(form);
      }
    });
    form.querySelectorAll("[data-rider-search]").forEach((control) => {
      control.addEventListener("input", () => applyTeamFiltersAndSort(form));
    });
    form.querySelectorAll("[data-team-filter], [data-sort-filter]").forEach((control) => {
      control.addEventListener("input", () => applyTeamFiltersAndSort(form));
      control.addEventListener("change", () => applyTeamFiltersAndSort(form));
    });
    form.querySelectorAll("[data-team-chip]").forEach((chip) => {
      chip.addEventListener("click", () => {
        const teamSelect = form.querySelector("[data-team-filter]");
        if (teamSelect) {
          teamSelect.value = chip.value;
        }
        applyTeamFiltersAndSort(form);
      });
    });
    form
      .querySelectorAll("[data-price-min-input], [data-price-max-input], [data-price-min-range], [data-price-max-range]")
      .forEach((control) => {
        control.addEventListener("input", () => {
          syncPriceControls(form, control);
          applyTeamFiltersAndSort(form);
        });
        control.addEventListener("change", () => {
          syncPriceControls(form, control);
          applyTeamFiltersAndSort(form);
        });
      });
    form.querySelectorAll("[data-reset-filters]").forEach((button) => {
      button.addEventListener("click", () => resetTeamFilters(form));
    });
    syncPriceControls(form);
    applyTeamFiltersAndSort(form);
    updateTeamForm(form);
  });

  document.querySelectorAll("[data-lineup-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      saveStageLineup(form);
    });
    form.addEventListener("change", (event) => {
      if (event.target.matches("[data-lineup-checkbox], [data-captain-radio]")) {
        syncLineupSelection(form);
      } else {
        updateLineupForm(form);
      }
    });
    form.addEventListener("click", (event) => {
      const profileButton = event.target.closest("[data-toggle-lineup-profile]");
      if (profileButton) {
        event.preventDefault();
        const card = profileButton.closest("[data-lineup-card]");
        if (card) {
          preserveScroll(() => toggleLineupRiderProfile(card, form));
        }
        return;
      }

      if (event.target.closest("[data-lineup-profile]")) {
        return;
      }

      const captainButton = event.target.closest("[data-toggle-captain]");
      if (captainButton) {
        event.preventDefault();
        const card = captainButton.closest("[data-lineup-card]");
        if (card) {
          setCaptain(card, form);
        }
        return;
      }

      const toggleButton = event.target.closest("[data-toggle-lineup]");
      if (toggleButton) {
        event.preventDefault();
        const card = toggleButton.closest("[data-lineup-card]");
        if (card) {
          toggleLineupCard(card, form);
        }
        return;
      }

      const card = event.target.closest("[data-lineup-card]");
      if (card && !event.target.closest("button")) {
        toggleLineupCard(card, form);
      }
    });
    form.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      const card = event.target.closest("[data-lineup-card]");
      if (!card || event.target.closest("button")) {
        return;
      }
      event.preventDefault();
      toggleLineupCard(card, form);
    });
    updateLineupForm(form);
  });

  document.querySelectorAll("[data-admin-job-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      startAdminJob(form);
    });
  });

  const deadlineMeters = Array.from(document.querySelectorAll("[data-deadline-at]"));
  if (deadlineMeters.length > 0) {
    const padTime = (value) => String(value).padStart(2, "0");
    const updateDeadlines = () => {
      const now = Date.now();
      deadlineMeters.forEach((meter) => {
        const deadline = Number(meter.dataset.deadlineAt);
        const countdown = meter.querySelector("[data-deadline-countdown]");
        const state = meter.querySelector(".deadline-state");
        if (!countdown || !Number.isFinite(deadline)) {
          return;
        }

        const remainingMilliseconds = deadline - now;
        if (remainingMilliseconds <= 0) {
          countdown.textContent = "Deadline verstreken";
          meter.dataset.deadlineState = "closed";
          if (state) {
            state.textContent = "Gesloten";
          }
          if (meter.dataset.hideTeamTabOnExpiry === "1") {
            document.querySelector("[data-team-selection-tab]")?.remove();
          }
          return;
        }

        const remainingSeconds = Math.ceil(remainingMilliseconds / 1000);
        const days = Math.floor(remainingSeconds / 86400);
        const hours = Math.floor((remainingSeconds % 86400) / 3600);
        const minutes = Math.floor((remainingSeconds % 3600) / 60);
        const seconds = remainingSeconds % 60;
        const clock = `${padTime(hours)}:${padTime(minutes)}:${padTime(seconds)}`;
        countdown.textContent = days > 0 ? `Nog ${days}d ${clock}` : `Nog ${clock}`;
        meter.dataset.deadlineState = remainingMilliseconds <= 3600000 ? "urgent" : "open";
        if (state) {
          state.textContent = "Open";
        }
      });
    };

    updateDeadlines();
    window.setInterval(updateDeadlines, 1000);
  }

  if (document.querySelector("[data-stage-selection-tab][data-stage-start-at]")) {
    updateStageNavigationLifecycle();
    window.setInterval(updateStageNavigationLifecycle, 1000);
  }

})();
