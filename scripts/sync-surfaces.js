// Keep file-based hosts and the separately installable ClawHub bundles in step.
const fs = require('node:fs');
const path = require('node:path');
process.chdir(path.join(__dirname, '..'));
const checking = process.argv.includes('--check');
function emit(file, contents) {
  if (checking) {
    if (!fs.existsSync(file) || !fs.readFileSync(file).equals(Buffer.from(contents))) {
      throw Error('Stale host surface: ' + file);
    }
  } else {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, contents);
  }
}
function bundle(source, dest) {
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || entry.name === '__pycache__') continue;
    const from = path.join(source, entry.name);
    const to = path.join(dest, entry.name);
    if (entry.isDirectory()) bundle(from, to);
    else emit(to, fs.readFileSync(from));
  }
}
for (const entry of fs.readdirSync('skills', { withFileTypes: true })) {
  if (!entry.isDirectory()) continue;
  const name = entry.name;
  const dir = path.join('skills', name);
  const skill = fs.readFileSync(path.join(dir, 'SKILL.md'), 'utf8');
  const description = skill.match(/^description: (.+)$/m)[1];
  const body = skill.replace(/^---[\s\S]*?---\s*/, '').trim();
  bundle(dir, path.join('.openclaw/skills', name));
  const location = 'Bundled skill directory: skills/' + name + '. Resolve its resources there.';
  emit('.opencode/command/' + name + '.md', '---\ndescription: ' + description + '\n---\n\n' + (name === 'mullet' ? 'Switch to mullet $ARGUMENTS mode.\n\n' : '') + location + '\n\n' + body + '\n');
  emit('commands/' + name + '.toml', 'description = ' + JSON.stringify(description) +
    '\nprompt = ' + JSON.stringify(location + '\n\n' + body + '\n\nUser arguments: {{args}}') + '\n');
}
const canonical = fs.readFileSync('AGENTS.md', 'utf8');
for (const file of ['.clinerules/mullet.md','.agents/rules/mullet.md','.cursor/rules/mullet.mdc',
  '.qoder/rules/mullet.md','.windsurf/rules/mullet.md','.github/copilot-instructions.md','.kiro/steering/mullet.md']) {
  const header = fs.readFileSync(file, 'utf8').match(/^---[\s\S]*?---\n/)?.[0] || '';
  emit(file, header + canonical);
}
