const http = require('http');
const { exec } = require('child_process');

const URL = 'http://localhost:3000';
const MAX_WAIT = 30000;
const INTERVAL = 500;

let elapsed = 0;

function check() {
  http.get(URL, (res) => {
    if (res.statusCode >= 200 && res.statusCode < 400) {
      printBanner();
      openBrowser();
    } else {
      retry();
    }
    res.resume();
  }).on('error', retry);
}

function retry() {
  elapsed += INTERVAL;
  if (elapsed < MAX_WAIT) {
    setTimeout(check, INTERVAL);
  } else {
    printBanner();
    console.log('  [!] Auto-open timed out, please open manually.\n');
  }
}

function printBanner() {
  console.log('\n');
  console.log('  ╔══════════════════════════════════════════╗');
  console.log('  ║                                          ║');
  console.log('  ║        LumenX Studio is ready!           ║');
  console.log('  ║                                          ║');
  console.log('  ║   Frontend:  http://localhost:3000       ║');
  console.log('  ║   Backend:   http://localhost:17177      ║');
  console.log('  ║                                          ║');
  console.log('  ║   Press Ctrl+C to stop all services.     ║');
  console.log('  ║                                          ║');
  console.log('  ╚══════════════════════════════════════════╝');
  console.log('\n');
}

function openBrowser() {
  const cmd = process.platform === 'win32' ? `start "" "${URL}"`
    : process.platform === 'darwin' ? `open "${URL}"`
    : `xdg-open "${URL}"`;
  exec(cmd);
}

check();
