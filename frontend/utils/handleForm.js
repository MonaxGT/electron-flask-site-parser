const { ipcRenderer, remote } = require("electron");

const form = document.querySelector("form.param-form");
const radio_buttons = form.querySelectorAll(".site-select input");
const max_pages_input = form.querySelector("#max-pages")
const textarea = form.querySelector("#search-terms");
const submit_btn = form.querySelector("#submit-params");
const successVisual = form.querySelector(".success-visual");
const failedVisual = form.querySelector(".failed-visual");
const progressVisual = form.querySelector(".progress-visual");

form.addEventListener("submit", (e) => {
  e.preventDefault();

  getFileUserSelection().then((userSelection) => {
    if (!userSelection.canceled) {
      submit_btn.disabled = true;
      successVisual.classList.add("hidden");
      failedVisual.classList.add("hidden");
      progressVisual.classList.remove("hidden");

      let site = null;
      for (radio of radio_buttons) {
        if (radio.checked) {
          site = radio.id;
          break;
        }
      }

      let search_terms = textarea.value;
      let max_pages = max_pages_input.value

      let path = userSelection.filePath;
     
      ipcRenderer.send("parse-with-params", { site, search_terms, max_pages, path });
    }
  });
});

ipcRenderer.on("parsing-complete", (e, {success, status, data, error}) => {
  submit_btn.disabled = false;
  progressVisual.classList.add("hidden");

  if (success) {
    successVisual.classList.remove("hidden");
    for (radio of radio_buttons) {
      if (radio.checked) {
        radio.checked = false;
        break;
      }
    }
    max_pages_input.value = 100
    textarea.value = "";
  } else {
    failedVisual.classList.remove("failed-visual");
    console.error({status, data, error})
  }
});

async function getFileUserSelection() {
  return await remote.dialog.showSaveDialog({
    title: "Выберите путь для сохранения файла результатов",
    defaultPath: "messages.xlsx",
    filters: [{ name: "Excel workbook", extensions: ["xlsx", "xlsm"] }],
    properties: ["createDirectory", "showOverwriteConfirmation"],
  });
}
