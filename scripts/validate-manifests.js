#!/usr/bin/env node
// Validate every packages/**/manifest.json against packages/_schema/manifest.schema.json.
// Also checks that id === folder-slug and author === parent-folder.
// Exits 1 on any failure. Used locally and in CI (validate.yml).

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const PKG_DIR = path.join(ROOT, 'packages');
const SCHEMA_PATH = path.join(PKG_DIR, '_schema', 'manifest.schema.json');

function loadSchema() {
  return JSON.parse(fs.readFileSync(SCHEMA_PATH, 'utf8'));
}

// A tiny JSON Schema validator — covers the draft-07 features we use:
// type, required, properties, additionalProperties, enum, pattern,
// minLength, maxLength, minItems, maxItems, items.
// Not complete — deliberate. Keeps CI zero-dep.
function validate(obj, schema, path = '') {
  const errs = [];
  const t = Array.isArray(obj) ? 'array' : obj === null ? 'null' : typeof obj;

  if (schema.type && schema.type !== t) {
    errs.push(`${path || '(root)'}: expected ${schema.type}, got ${t}`);
    return errs;
  }

  if (schema.enum && !schema.enum.includes(obj)) {
    errs.push(`${path}: ${JSON.stringify(obj)} not in [${schema.enum.join(', ')}]`);
  }

  if (t === 'string') {
    if (schema.minLength != null && obj.length < schema.minLength) errs.push(`${path}: shorter than ${schema.minLength}`);
    if (schema.maxLength != null && obj.length > schema.maxLength) errs.push(`${path}: longer than ${schema.maxLength}`);
    if (schema.pattern && !new RegExp(schema.pattern).test(obj)) errs.push(`${path}: does not match /${schema.pattern}/`);
  }

  if (t === 'array') {
    if (schema.minItems != null && obj.length < schema.minItems) errs.push(`${path}: fewer than ${schema.minItems} items`);
    if (schema.maxItems != null && obj.length > schema.maxItems) errs.push(`${path}: more than ${schema.maxItems} items`);
    if (schema.items) obj.forEach((el, i) => errs.push(...validate(el, schema.items, `${path}[${i}]`)));
  }

  if (t === 'object') {
    if (schema.required) {
      for (const key of schema.required) {
        if (!(key in obj)) errs.push(`${path || '(root)'}: missing required "${key}"`);
      }
    }
    if (schema.properties) {
      for (const [key, sub] of Object.entries(schema.properties)) {
        if (key in obj) errs.push(...validate(obj[key], sub, path ? `${path}.${key}` : key));
      }
    }
    if (schema.additionalProperties === false && schema.properties) {
      const allowed = new Set(Object.keys(schema.properties));
      for (const key of Object.keys(obj)) {
        if (!allowed.has(key)) errs.push(`${path || '(root)'}: unknown property "${key}"`);
      }
    }
  }

  return errs;
}

function walkManifests(dir) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const author of fs.readdirSync(dir)) {
    if (author.startsWith('_') || author.startsWith('.')) continue;
    const authorPath = path.join(dir, author);
    if (!fs.statSync(authorPath).isDirectory()) continue;
    for (const slug of fs.readdirSync(authorPath)) {
      const slugPath = path.join(authorPath, slug);
      if (!fs.statSync(slugPath).isDirectory()) continue;
      const manifestPath = path.join(slugPath, 'manifest.json');
      if (fs.existsSync(manifestPath)) {
        out.push({ author, slug, manifestPath, slugPath });
      }
    }
  }
  return out;
}

function main() {
  const schema = loadSchema();
  const manifests = walkManifests(PKG_DIR);

  if (manifests.length === 0) {
    console.log('No manifests found under packages/. That is OK for an empty seed.');
    return;
  }

  let totalErrs = 0;
  for (const { author, slug, manifestPath, slugPath } of manifests) {
    let data;
    try {
      data = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    } catch (e) {
      console.error(`[FAIL] ${manifestPath}: invalid JSON — ${e.message}`);
      totalErrs++;
      continue;
    }

    const errs = validate(data, schema);

    // Structural checks beyond schema.
    if (data.id !== slug) errs.push(`id "${data.id}" does not match folder slug "${slug}"`);
    if (data.author !== author) errs.push(`author "${data.author}" does not match parent folder "${author}"`);
    if (!fs.existsSync(path.join(slugPath, 'README.md'))) errs.push(`missing README.md`);
    if (data.distribution === 'redirect' && !data.redirectUrl) errs.push(`distribution is "redirect" but redirectUrl is missing`);

    if (errs.length) {
      console.error(`[FAIL] ${author}/${slug}:`);
      for (const e of errs) console.error(`  - ${e}`);
      totalErrs += errs.length;
    } else {
      console.log(`[OK]   ${author}/${slug}`);
    }
  }

  console.log(`\n${manifests.length} manifest(s), ${totalErrs} error(s).`);
  if (totalErrs) process.exit(1);
}

if (require.main === module) main();
module.exports = { validate, walkManifests, loadSchema };
