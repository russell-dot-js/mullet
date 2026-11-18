// OpenCode 2 loads this file automatically from .opencode/plugins/ and does not
// read mullet.mjs next to it, so keep the one-line entry here. npm consumers
// never see it: package.json main/exports still point at mullet.mjs.
export { default } from './mullet.mjs'
