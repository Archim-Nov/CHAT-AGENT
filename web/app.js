const sendBtn = document.getElementById("send-btn");
const userInput = document.getElementById("user-input");
const replyEl = document.getElementById("reply");
const emotionEl = document.getElementById("emotion");
const variablesEl = document.getElementById("variables");
const apiBaseInput = document.getElementById("api-base");
const apiKeyInput = document.getElementById("api-key");
const mainModelInput = document.getElementById("main-model");
const emotionModelInput = document.getElementById("emotion-model");
const systemModelInput = document.getElementById("system-model");
const saveSettingsBtn = document.getElementById("save-settings");
const clearSettingsBtn = document.getElementById("clear-settings");
const settingsFeedback = document.getElementById("settings-feedback");

const STORAGE_KEY = "mcp-agent-settings";
let feedbackTimeout;

const readSettingsFromStorage = () => {
  try {
    const serialized = window.sessionStorage.getItem(STORAGE_KEY);
    if (!serialized) {
      return {};
    }
    return JSON.parse(serialized);
  } catch (error) {
    console.warn("Unable to read stored settings", error);
    return {};
  }
};

const writeSettingsToStorage = (settings) => {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch (error) {
    console.warn("Unable to persist settings", error);
  }
};

const clearSettingsFromStorage = () => {
  try {
    window.sessionStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.warn("Unable to clear stored settings", error);
  }
};

const applySettingsToInputs = (settings) => {
  apiBaseInput.value = settings.apiBase || "";
  apiKeyInput.value = settings.apiKey || "";
  mainModelInput.value = settings.mainModel || "";
  emotionModelInput.value = settings.emotionModel || "";
  systemModelInput.value = settings.systemModel || "";
};

const collectSettings = () => ({
  apiBase: apiBaseInput.value.trim(),
  apiKey: apiKeyInput.value.trim(),
  mainModel: mainModelInput.value.trim(),
  emotionModel: emotionModelInput.value.trim(),
  systemModel: systemModelInput.value.trim(),
});

const showSettingsFeedback = (message) => {
  window.clearTimeout(feedbackTimeout);
  settingsFeedback.textContent = message;
  feedbackTimeout = window.setTimeout(() => {
    settingsFeedback.textContent = "";
  }, 3200);
};

const loadSettingsOnStartup = () => {
  const settings = readSettingsFromStorage();
  applySettingsToInputs(settings);
};

const updateResults = (data) => {
  replyEl.textContent = data.reply || "No reply";
  emotionEl.textContent = data.emotion || "No emotion data";
  variablesEl.textContent = data.variables || "No variables extracted";
};

const setLoading = (isLoading) => {
  sendBtn.disabled = isLoading;
  sendBtn.textContent = isLoading ? "Loading..." : "Send";
};

const sendMessage = async () => {
  const message = userInput.value.trim();
  if (!message) {
    alert("Please enter a message before sending.");
    return;
  }

  const settings = collectSettings();
  setLoading(true);
  updateResults({ reply: "…", emotion: "…", variables: "…" });

  try {
    const payload = { message };

    if (settings.apiKey) {
      payload.api_key = settings.apiKey;
    }
    if (settings.apiBase) {
      payload.api_base = settings.apiBase;
    }
    if (settings.mainModel) {
      payload.main_model = settings.mainModel;
    }
    if (settings.emotionModel) {
      payload.emotion_model = settings.emotionModel;
    }
    if (settings.systemModel) {
      payload.system_model = settings.systemModel;
    }

    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Unknown error");
    }

    const data = await response.json();
    updateResults(data);
  } catch (error) {
    updateResults({
      reply: `Error: ${error.message}`,
      emotion: "Unable to perform emotion analysis.",
      variables: "Unable to extract variables.",
    });
  } finally {
    setLoading(false);
  }
};

saveSettingsBtn.addEventListener("click", () => {
  const settings = collectSettings();
  writeSettingsToStorage(settings);
  showSettingsFeedback("Settings saved for this session.");
});

clearSettingsBtn.addEventListener("click", () => {
  clearSettingsFromStorage();
  applySettingsToInputs({});
  showSettingsFeedback("Settings cleared.");
});

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
    sendMessage();
  }
});

loadSettingsOnStartup();
