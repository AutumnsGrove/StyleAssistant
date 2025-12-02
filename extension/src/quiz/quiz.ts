/**
 * Quiz page script for GroveAssistant.
 *
 * Handles:
 * - Multi-step quiz navigation
 * - Answer collection and validation
 * - Profile generation and submission
 */

import { getSettings } from "../shared/storage";

/** Profile data structure matching backend expectations */
interface ProfileData {
  fit_preferences: string[];
  color_palette: string[];
  style_goals: string[];
  body_type: string | null;
  priorities: string[];
  avoidances: string[];
}

/** Quiz state */
interface QuizState {
  currentQuestion: number;
  totalQuestions: number;
  answers: {
    fit: string[];
    color: string[];
    formality: number;
    presentation: string[];
    aesthetic: string[];
    priority: string[];
    avoid: string[];
  };
}

// Initialize state
const state: QuizState = {
  currentQuestion: 1,
  totalQuestions: 7,
  answers: {
    fit: [],
    color: [],
    formality: 5,
    presentation: [],
    aesthetic: [],
    priority: [],
    avoid: [],
  },
};

// DOM elements
const elements = {
  progressFill: document.getElementById("progress-fill") as HTMLElement,
  progressText: document.getElementById("progress-text") as HTMLElement,
  btnBack: document.getElementById("btn-back") as HTMLButtonElement,
  btnNext: document.getElementById("btn-next") as HTMLButtonElement,
  formalitySlider: document.getElementById("formality-slider") as HTMLInputElement,
  formalityValue: document.getElementById("formality-value") as HTMLElement,
  formalityDesc: document.getElementById("formality-desc") as HTMLElement,
  priorityCount: document.getElementById("priority-count") as HTMLElement,
  loadingOverlay: document.getElementById("loading-overlay") as HTMLElement,
  errorToast: document.getElementById("error-toast") as HTMLElement,
  errorMessage: document.getElementById("error-message") as HTMLElement,
  errorClose: document.getElementById("error-close") as HTMLButtonElement,
  profileSummary: document.getElementById("profile-summary") as HTMLElement,
};

/** Formality descriptions by level */
const formalityDescriptions: Record<number, string> = {
  1: "Very casual - loungewear, athleisure",
  2: "Casual - relaxed everyday wear",
  3: "Casual-leaning - comfortable but put-together",
  4: "Smart casual - polished casual looks",
  5: "Smart casual - versatile everyday style",
  6: "Business casual - office-appropriate",
  7: "Business casual - professional polish",
  8: "Semi-formal - dressy occasions",
  9: "Formal - business professional",
  10: "Very formal - suits, evening wear",
};

/**
 * Update progress bar and text.
 */
function updateProgress(): void {
  const percent = ((state.currentQuestion - 1) / state.totalQuestions) * 100;
  elements.progressFill.style.width = `${percent}%`;

  if (state.currentQuestion <= state.totalQuestions) {
    elements.progressText.textContent = `Question ${state.currentQuestion} of ${state.totalQuestions}`;
  } else {
    elements.progressText.textContent = "Complete!";
    elements.progressFill.style.width = "100%";
  }
}

/**
 * Show a specific question section.
 */
function showQuestion(questionNum: number): void {
  // Hide all questions
  document.querySelectorAll(".question-section").forEach((section) => {
    (section as HTMLElement).style.display = "none";
  });

  // Show target question or completion
  if (questionNum > state.totalQuestions) {
    const completion = document.getElementById("completion");
    if (completion) completion.style.display = "block";
    elements.btnNext.textContent = "Close";
    elements.btnBack.style.visibility = "hidden";
  } else {
    const target = document.getElementById(`q${questionNum}`);
    if (target) target.style.display = "block";
    elements.btnNext.textContent = questionNum === state.totalQuestions ? "Finish" : "Next";
    elements.btnBack.style.visibility = questionNum === 1 ? "hidden" : "visible";
  }

  updateProgress();
}

/**
 * Collect answers from current question.
 */
function collectCurrentAnswers(): void {
  const q = state.currentQuestion;

  switch (q) {
    case 1:
      state.answers.fit = getCheckedValues("fit");
      break;
    case 2:
      state.answers.color = getCheckedValues("color");
      break;
    case 3:
      state.answers.formality = parseInt(elements.formalitySlider.value, 10);
      break;
    case 4:
      state.answers.presentation = getCheckedValues("presentation");
      break;
    case 5:
      state.answers.aesthetic = getCheckedValues("aesthetic");
      break;
    case 6:
      state.answers.priority = getCheckedValues("priority");
      break;
    case 7:
      state.answers.avoid = getCheckedValues("avoid");
      break;
  }
}

/**
 * Get all checked checkbox values for a given name.
 */
function getCheckedValues(name: string): string[] {
  const checkboxes = document.querySelectorAll<HTMLInputElement>(
    `input[name="${name}"]:checked`
  );
  return Array.from(checkboxes).map((cb) => cb.value);
}

/**
 * Validate current question has required answers.
 */
function validateCurrentQuestion(): boolean {
  const q = state.currentQuestion;

  switch (q) {
    case 1:
      return getCheckedValues("fit").length > 0;
    case 2:
      return getCheckedValues("color").length > 0;
    case 3:
      return true; // Slider always has a value
    case 4:
      return getCheckedValues("presentation").length > 0;
    case 5:
      return getCheckedValues("aesthetic").length > 0;
    case 6: {
      const priorities = getCheckedValues("priority");
      return priorities.length >= 1 && priorities.length <= 3;
    }
    case 7:
      return true; // Avoidances are optional
    default:
      return true;
  }
}

/**
 * Build style_goals from formality, presentation, and aesthetics.
 */
function buildStyleGoals(): string[] {
  const goals: string[] = [];

  // Add formality-based goals
  const formality = state.answers.formality;
  if (formality <= 3) {
    goals.push("casual");
  } else if (formality <= 6) {
    goals.push("smart_casual");
  } else {
    goals.push("formal");
  }

  // Add presentation preferences
  goals.push(...state.answers.presentation);

  // Add aesthetic preferences
  goals.push(...state.answers.aesthetic);

  return goals;
}

/**
 * Convert quiz answers to profile data.
 */
function buildProfileData(): ProfileData {
  return {
    fit_preferences: state.answers.fit,
    color_palette: state.answers.color,
    style_goals: buildStyleGoals(),
    body_type: null, // Could be extended with optional question
    priorities: state.answers.priority,
    avoidances: state.answers.avoid,
  };
}

/**
 * Save profile to backend.
 */
async function saveProfile(profile: ProfileData): Promise<void> {
  const settings = await getSettings();
  const url = `${settings.apiEndpoint}/api/profile`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(profile),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
}

/**
 * Display profile summary on completion screen.
 */
function displayProfileSummary(): void {
  const profile = buildProfileData();

  const summaryHtml = `
    <div class="summary-section">
      <h4>Fit Preferences</h4>
      <p>${profile.fit_preferences.join(", ") || "None selected"}</p>
    </div>
    <div class="summary-section">
      <h4>Color Palette</h4>
      <p>${profile.color_palette.map(c => c.replace(/_/g, " ")).join(", ") || "None selected"}</p>
    </div>
    <div class="summary-section">
      <h4>Style Goals</h4>
      <p>${profile.style_goals.map(g => g.replace(/_/g, " ")).join(", ") || "None selected"}</p>
    </div>
    <div class="summary-section">
      <h4>Top Priorities</h4>
      <p>${profile.priorities.map(p => p.replace(/_/g, " ")).join(", ") || "None selected"}</p>
    </div>
    ${profile.avoidances.length > 0 ? `
    <div class="summary-section">
      <h4>Things to Avoid</h4>
      <p>${profile.avoidances.map(a => a.replace(/_/g, " ")).join(", ")}</p>
    </div>
    ` : ""}
  `;

  elements.profileSummary.innerHTML = summaryHtml;
}

/**
 * Show error toast.
 */
function showError(message: string): void {
  elements.errorMessage.textContent = message;
  elements.errorToast.style.display = "flex";

  setTimeout(() => {
    elements.errorToast.style.display = "none";
  }, 5000);
}

/**
 * Handle next button click.
 */
async function handleNext(): Promise<void> {
  // If on completion screen, close the tab
  if (state.currentQuestion > state.totalQuestions) {
    window.close();
    return;
  }

  // Validate current question
  if (!validateCurrentQuestion()) {
    showError("Please make at least one selection to continue.");
    return;
  }

  // Collect answers from current question
  collectCurrentAnswers();

  // If finishing quiz, save profile
  if (state.currentQuestion === state.totalQuestions) {
    elements.loadingOverlay.style.display = "flex";

    try {
      const profile = buildProfileData();
      await saveProfile(profile);
      displayProfileSummary();
      state.currentQuestion++;
      showQuestion(state.currentQuestion);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save profile";
      showError(message);
    } finally {
      elements.loadingOverlay.style.display = "none";
    }
    return;
  }

  // Move to next question
  state.currentQuestion++;
  showQuestion(state.currentQuestion);
}

/**
 * Handle back button click.
 */
function handleBack(): void {
  if (state.currentQuestion > 1) {
    collectCurrentAnswers();
    state.currentQuestion--;
    showQuestion(state.currentQuestion);
  }
}

/**
 * Update formality slider display.
 */
function updateFormalityDisplay(): void {
  const value = parseInt(elements.formalitySlider.value, 10);
  elements.formalityValue.textContent = value.toString();
  elements.formalityDesc.textContent = formalityDescriptions[value] || "";
}

/**
 * Update priority selection count.
 */
function updatePriorityCount(): void {
  const count = getCheckedValues("priority").length;
  elements.priorityCount.textContent = `${count} of 3 selected`;

  // Visual feedback for limit
  if (count >= 3) {
    elements.priorityCount.classList.add("limit-reached");
  } else {
    elements.priorityCount.classList.remove("limit-reached");
  }
}

/**
 * Enforce max selection limit on priority checkboxes.
 */
function enforcePriorityLimit(): void {
  const checkboxes = document.querySelectorAll<HTMLInputElement>('input[name="priority"]');
  const checkedCount = getCheckedValues("priority").length;

  checkboxes.forEach((cb) => {
    if (!cb.checked && checkedCount >= 3) {
      cb.disabled = true;
      cb.closest(".option-card")?.classList.add("disabled");
    } else {
      cb.disabled = false;
      cb.closest(".option-card")?.classList.remove("disabled");
    }
  });

  updatePriorityCount();
}

/**
 * Initialize quiz.
 */
function init(): void {
  // Set up navigation buttons
  elements.btnNext.addEventListener("click", handleNext);
  elements.btnBack.addEventListener("click", handleBack);

  // Set up formality slider
  elements.formalitySlider.addEventListener("input", updateFormalityDisplay);
  updateFormalityDisplay();

  // Set up priority limit enforcement
  document.querySelectorAll('input[name="priority"]').forEach((cb) => {
    cb.addEventListener("change", enforcePriorityLimit);
  });

  // Set up error toast close
  elements.errorClose.addEventListener("click", () => {
    elements.errorToast.style.display = "none";
  });

  // Show first question
  showQuestion(1);

  console.log("[GroveAssistant] Quiz initialized");
}

// Initialize on load
document.addEventListener("DOMContentLoaded", init);
