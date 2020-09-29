const electron = require("electron");
const axios = require("axios");
const path = require("path");

const MainMenuTemplate = require("./frontend/templates/mainMenuTemplate");
const startServer = require("./startServer");

const { app, BrowserWindow, Menu, ipcMain } = electron;

try {
  require("electron-reload")(__dirname);
} catch (error) {
  console.warn(
    "Hot reload is disabled. If you expect it to be enabled, check if npm package electron-reload is installed"
  );
}

let mainWindow;
let server_finalize;
app.on("ready", () => {
  server_finalize = startServer()

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

  ipcMain.on("parse-with-params", (e, data) => {
    /* TODO parsing */
    axios
      .post(`http://127.0.0.1:5000/messages/${data.site}`, {
        filename: data.path,
        keywords: data.search_terms,
        one_search_page_only: true,
      })
      .then(
        (responce) => {
          e.sender.send("parsing-complete", {
            success: responce.status == 201,
            status: responce.status,
            data: responce.data,
          });
        },
        (error) => {
          console.error(e);
          e.sender.send("parsing-complete", { success: false, error: error });
        }
      )
      .catch((e) => console.log(e));
  });
});

app.on("window-all-closed", () => {
  console.log('Exiting server...')
  server_finalize();
});
