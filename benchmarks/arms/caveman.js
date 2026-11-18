// Read the installed comparison skill so its version and license stay with its owner.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
module.exports = ({ vars }) => {
  const skill = process.env.CAVEMAN_SKILL || path.join(os.homedir(), '.agents/skills/caveman/SKILL.md');
  return [
    { role: 'system', content: fs.readFileSync(skill, 'utf8') },
    { role: 'user', content: vars.task },
  ];
};
