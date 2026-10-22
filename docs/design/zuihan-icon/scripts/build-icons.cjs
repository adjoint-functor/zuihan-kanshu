#!/usr/bin/env node
'use strict';

// Requires Node.js >= 20.9 and sharp 0.34.x/0.35.x. No network or image generation.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const sharp = require('sharp');

const ROOT = path.resolve(__dirname, '..');
const option = { source: path.join(ROOT, 'source/approved-master.svg'), outDir: ROOT, reviewDir: path.join(ROOT, 'review'), report: path.join(ROOT, 'build-report.json'), pngOnly: false, skipReview: false };
for (let i = 2; i < process.argv.length; i++) {
  const key = process.argv[i];
  if (key === '--source') option.source = path.resolve(process.argv[++i]);
  else if (key === '--out-dir') option.outDir = path.resolve(process.argv[++i]);
  else if (key === '--review-dir') option.reviewDir = path.resolve(process.argv[++i]);
  else if (key === '--report') option.report = path.resolve(process.argv[++i]);
  else if (key === '--png-only') option.pngOnly = true;
  else if (key === '--skip-review') option.skipReview = true;
  else if (key === '--help') {
    console.log('node build-icons.cjs [--source approved-master.svg] [--out-dir DIR] [--review-dir DIR] [--report FILE] [--png-only] [--skip-review]');
    process.exit(0);
  } else throw new Error(`Unknown option: ${key}`);
}

const BRAND = { primary: '#087F79', onDark: '#64D5C7', previewLight: '#F5F3ED', previewDark: '#101C1C' };
const DARK_EXPONENT = 0.92;
const SVG_ROOT = 'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1024" height="1024" viewBox="-85.5 -85.5 1425 1425" role="img" aria-labelledby="title desc"';

function extract(source) {
  const definitions = source.match(/<defs>([\s\S]*?)<\/defs>/)?.[1];
  const image = source.match(/<image\b[^>]*id="unchanged-original-png"[^>]*\/>/)?.[0];
  const relief = source.match(/<g id="exact-mathematical-relief">[\s\S]*?(?=\n<\/svg>)/)?.[0];
  assert(definitions && image && relief, 'Expected approved self-contained source structure');
  const ids = [...definitions.matchAll(/<g id="(formula-[^"]+)"/g)].map(m => m[1]);
  const engravings = [...relief.matchAll(/<g id="engraving-\d+" data-formula="([^"]+)" data-copy="(\d+)"/g)];
  assert.equal(ids.length, 22, '22 vector formula definitions required');
  assert.equal(engravings.length, 88, '88 approved formula placements required');
  assert.equal((relief.match(/<use href="#formula-/g) || []).length, 264, 'Each placement retains three relief passes');
  for (const id of ids) assert.equal(engravings.filter(e => `formula-${e[1]}` === id).length, 4, `${id} must occur four times`);
  assert(!/<(?:text|script|foreignObject)\b/i.test(definitions + relief), 'Formula layer must remain native paths');
  return { definitions, image, relief, ids };
}

function compose(parts, dark) {
  const filter = dark ? `\n<filter id="dark-material-lift" filterUnits="userSpaceOnUse" x="0" y="0" width="1254" height="1254" color-interpolation-filters="sRGB">\n  <feComponentTransfer>\n    <feFuncR type="gamma" amplitude="1" exponent="${DARK_EXPONENT}" offset="0"/>\n    <feFuncG type="gamma" amplitude="1" exponent="${DARK_EXPONENT}" offset="0"/>\n    <feFuncB type="gamma" amplitude="1" exponent="${DARK_EXPONENT}" offset="0"/>\n    <feFuncA type="identity"/>\n  </feComponentTransfer>\n</filter>\n` : '';
  const image = dark ? parts.image.replace('/>', ' filter="url(#dark-material-lift)"/>') : parts.image;
  return `<?xml version="1.0" encoding="UTF-8"?>\n<svg ${SVG_ROOT}>\n<title id="title">瑞般观珠${dark ? ' — 深色背景适配' : ''}</title>\n<desc id="desc">Approved matte champagne pearl, teal metallic lotus leaves and Buddhist relief. 22 exact vector formulas, four complete placements each. Embedded original PNG and formula paths/placements remain unchanged. Transparent background.${dark ? ' Same geometry and alpha; only the image RGB receives a gentle gamma lift. Formula layer is outside the filter.' : ''}</desc>\n<metadata>{"productionSource":"source/approved-master.svg","formulaDefinitions":22,"formulaPlacements":88,"reliefPasses":264,"variant":"${dark ? 'dark' : 'normal'}","brand":"${BRAND.primary}","darkRgbGamma":${dark ? DARK_EXPONENT : 1},"alphaMask":"original, unchanged"}</metadata>\n<defs>${parts.definitions}${filter}</defs>\n${image}\n${parts.relief}\n</svg>\n`;
}

async function render(svg, size) {
  return sharp(Buffer.from(svg), { density: 144 }).resize(size, size, { fit: 'fill', kernel: sharp.kernel.lanczos3 }).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
}

function getAlpha(raw) {
  const alpha = Buffer.alloc(raw.length / 4);
  for (let i = 0, j = 3; j < raw.length; i++, j += 4) alpha[i] = raw[j];
  return alpha;
}

function setAlpha(raw, alpha) {
  for (let i = 0, j = 3; j < raw.length; i++, j += 4) raw[j] = alpha[i];
}

function xml(s) { return s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
function label(text, width = 580, color = '#223B38', size = 20) {
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="32"><text x="0" y="24" fill="${color}" font-family="sans-serif" font-size="${size}">${xml(text)}</text></svg>`);
}

async function review(pngs) {
  fs.mkdirSync(option.reviewDir, { recursive: true });
  const layers = [];
  for (let col = 0; col < 2; col++) {
    const dark = col === 1, dx = col * 620, background = dark ? BRAND.previewDark : BRAND.previewLight;
    const main = await sharp(pngs[`${dark ? 'dark-' : ''}1024`]).resize(512).flatten({background}).png().toBuffer();
    const small = await sharp(pngs[`${dark ? 'dark-' : ''}256`]).resize(128).flatten({background}).png().toBuffer();
    const tiny = await sharp(pngs[`${dark ? 'dark-' : ''}256`]).resize(48).flatten({background}).png().toBuffer();
    layers.push({input:label(`${dark ? 'DARK' : 'NORMAL'}  ·  ${background}`),left:dx+28,top:12});
    layers.push({input:{create:{width:600,height:740,channels:3,background}},left:dx+20,top:52});
    layers.push({input:main,left:dx+64,top:68});
    layers.push({input:small,left:dx+104,top:620});
    layers.push({input:tiny,left:dx+368,top:660});
    layers.push({input:label('128 px',140,dark ? '#D6EAE5' : '#294E48',16),left:dx+104,top:752});
    layers.push({input:label('48 px',140,dark ? '#D6EAE5' : '#294E48',16),left:dx+338,top:752});
  }
  layers.push({input:label('Same source, geometry and alpha. Exact formula paths preserved; microengraving is detail at large sizes.',1180,'#3B5751',17),left:28,top:810});
  await sharp({create:{width:1260,height:864,channels:3,background:'#E7EBE6'}}).composite(layers).png().toFile(path.join(option.reviewDir,'production-preview.png'));
}

async function main() {
  const source = fs.readFileSync(option.source, 'utf8');
  const parts = extract(source);
  const normal = compose(parts, false), dark = compose(parts, true);
  // These are direct string equalities, so the approved math is never regenerated.
  assert.equal(normal.match(/<defs>([\s\S]*?)<\/defs>/)[1], parts.definitions);
  assert(normal.includes(parts.relief) && dark.includes(parts.relief), 'Formula placement block must be unchanged');
  assert(normal.includes(parts.image), 'Original embedded PNG element must be unchanged');
  fs.mkdirSync(option.outDir, {recursive:true});
  if (!option.pngOnly) {
    fs.writeFileSync(path.join(option.outDir,'icon.svg'), normal);
    fs.writeFileSync(path.join(option.outDir,'icon-dark.svg'), dark);
  }
  const pngs = {}, files = [], alphaChecks = [];
  for (const size of [1024,256]) {
    const a = await render(normal,size), b = await render(dark,size);
    const alpha = getAlpha(a.data), darkAlphaBefore = getAlpha(b.data);
    let rendererRoundingPixels=0;
    for(let i=0;i<alpha.length;i++)if(alpha[i]!==darkAlphaBefore[i])rendererRoundingPixels++;
    // Native SVG filter surfaces can round alpha differently. The PNG dark output
    // explicitly reuses the normal alpha bytes; no geometry is inferred or redrawn.
    setAlpha(b.data, alpha);
    assert(getAlpha(b.data).equals(alpha),'Normal/dark alpha must be byte-identical');
    alphaChecks.push({size,identicalAlpha:true,rendererRoundingPixels});
    for (const [prefix,raw] of [['',a],['dark-',b]]) {
      const filename=`icon-${prefix}${size}.png`;
      const data=await sharp(raw.data,{raw:{width:size,height:size,channels:4}}).png({compressionLevel:9,palette:false}).toBuffer();
      assert(data.length<=5*1024*1024,`${filename} exceeds 5 MiB`);
      await fs.promises.writeFile(path.join(option.outDir,filename),data);
      pngs[`${prefix}${size}`]=data;
      files.push({file:filename,width:size,height:size,format:'png',channels:4,bytes:data.length,transparentPixels:alpha.filter(v=>v===0).length});
    }
  }
  if(!option.skipReview)await review(pngs);
  const report={source:path.relative(ROOT,option.source).replaceAll('\\','/'),brand:BRAND,formulaDefinitions:22,formulaPlacements:88,reliefPasses:264,formulaPathsAndPlacementsUnchanged:true,embeddedPngUnchanged:true,alphaMask:'Original alpha; no mask, erosion, threshold, or edge repaint',darkMaterialGamma:DARK_EXPONENT,alphaChecks,files,runtime:{node:process.versions.node,sharp:sharp.versions.sharp,vips:sharp.versions.vips}};
  fs.mkdirSync(path.dirname(option.report),{recursive:true});
  fs.writeFileSync(option.report,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
}

main().catch(error=>{console.error(error.stack || error);process.exit(1);});
