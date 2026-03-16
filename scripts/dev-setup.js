const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const isWindows = process.platform === 'win32';
const venvPython = path.join(root, '.venv', isWindows ? 'Scripts' : 'bin', isWindows ? 'python.exe' : 'python');
const frontendModules = path.join(root, 'frontend', 'node_modules');

// 检查 .venv 是否存在，不存在则创建并安装依赖
if (!fs.existsSync(venvPython)) {
  console.log('[setup] .venv not found, creating virtual environment...');
  execSync('python -m venv .venv', { cwd: root, stdio: 'inherit' });

  const pip = path.join(root, '.venv', isWindows ? 'Scripts' : 'bin', 'pip');
  console.log('[setup] Installing Python dependencies...');
  execSync(`"${pip}" install -r requirements.txt`, { cwd: root, stdio: 'inherit' });
  console.log('[setup] Python dependencies installed.');
}

// 检查前端 node_modules 是否存在
if (!fs.existsSync(frontendModules)) {
  console.log('[setup] frontend/node_modules not found, installing...');
  execSync('npm install', { cwd: path.join(root, 'frontend'), stdio: 'inherit' });
  console.log('[setup] Frontend dependencies installed.');
}
