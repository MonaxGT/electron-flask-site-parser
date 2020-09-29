const path = require("path");
const { existsSync } = require("fs");
const { spawn, execFile } = require("child_process");

const PY_DIST_FOLDER = "appdist";
const PY_FOLDER = "backend";
const PY_MODULE = "app";

const isPackaged = () => existsSync(path.join(__dirname, PY_DIST_FOLDER));

const getScriptPath = () => {
  if (!isPackaged()) {
    return path.join(__dirname, PY_FOLDER, PY_MODULE + ".py");
  }
  if (process.platform === "win32") {
    return path.join(__dirname, PY_DIST_FOLDER, PY_MODULE, PY_MODULE + ".exe");
  }
  return path.join(__dirname, PY_DIST_FOLDER, PY_MODULE, PY_MODULE);
};

const startServer = () => {
  let script = getScriptPath();
  let pyProc = null

  if (isPackaged()) {
    pyProc = execFile(script);
  } else {
    pyProc = spawn("python", [script]);
  }

  if (pyProc === null) {
    throw new Error("Failed to start python server");
  }

  console.log('Server started');
  return () => {
    pyProc.kill()
  }
};

module.exports = startServer;
