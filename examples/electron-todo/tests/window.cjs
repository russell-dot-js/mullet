const assert = require('node:assert/strict');
const { setTimeout: delay } = require('node:timers/promises');

module.exports = async function inspect(desk) {
  const evaluate = source => desk.webContents.executeJavaScript(source);
  async function waitFor(expression) {
    const deadline = Date.now() + 45000;
    while (Date.now() < deadline) {
      if (await evaluate(expression)) return;
      await delay(100);
    }
    throw Error('Counter timed out: ' + await evaluate('document.body.innerText'));
  }
  await waitFor("!document.querySelector('form').inert");
  await evaluate("document.querySelector('#title').value='Buy milk'; document.querySelector('#file').click()");
  await waitFor("!document.querySelector('form').inert && Boolean(document.querySelector('li button'))");
  await evaluate("document.querySelector('li button').click()");
  await waitFor("!document.querySelector('form').inert && document.querySelector('li button').disabled");
  const receipt = await evaluate("document.querySelector('#receipt').innerText");
  assert.equal((receipt.match(/200 hearings · 3200 policies/g) || []).length, 2);
  assert.match(await evaluate("document.querySelector('#bays').innerText"), /\[x\] Buy milk/);
  console.log(receipt);
};
