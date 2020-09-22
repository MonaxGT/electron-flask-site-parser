const electron = require("electron");
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
    console.log(data);
    await new Promise((r) => setTimeout(r, 3000));
    //*******************/

    e.sender.send("parsing-complete", /* success: */ true);
  });
});
