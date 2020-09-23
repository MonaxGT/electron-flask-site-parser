const electron = require("electron");
const axios = require("axios");
const path = require("path");

const MainMenuTemplate = require("./frontend/templates/mainMenuTemplate");

const { app, BrowserWindow, Menu, ipcMain } = electron;

try {
  require("electron-reload")(__dirname); // hot reload
} catch (error) {}

let mainWindow;
app.on("ready", () => {
  mainWindow = new BrowserWindow({
    webPreferences: {
      nodeIntegration: true,
      enableRemoteModule: true,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "frontend", "MainWindow.html"));

  const mainMenu = Menu.buildFromTemplate(MainMenuTemplate);
  Menu.setApplicationMenu(mainMenu);

  mainWindow.on("closed", () => {
    app.quit();
  });

  ipcMain.on("parse-with-params", async (e, data) => {
    /* TODO parsing */
    responce = await axios.post(`http://127.0.0.1:5000/messages/${data.site}`, {
      filename: data.path,
      keywords: data.search_terms,
      one_search_page_only: true
    });
    e.sender.send("parsing-complete", responce.status == 201);
  });
});
