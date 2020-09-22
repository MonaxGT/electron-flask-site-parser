const { app } = require("electron");

const MainMenuTemplate = [
  {
    label: "File",
    submenu: [
      {
        label: "Выйти",
        click: () => {
          app.quit();
        },
      },
    ],
  },
];

if (process.platform == "darwin") {
  MainMenuTemplate.unshift({});
}

MainMenuTemplate.push({
  label: "Developer Tools",
  submenu: [
    {
      label: "Toggle DevTools",
      accelerator: "Ctrl+I",
      click: (item, focusedWindow) => {
        focusedWindow.toggleDevTools();
      },
    },
    {
      role: "reload",
    },
  ],
});

module.exports = MainMenuTemplate;
