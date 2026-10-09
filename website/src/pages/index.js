// Landing page – the documentation itself lives under /docs/.
import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import CodeBlock from '@theme/CodeBlock';
import Translate, {translate} from '@docusaurus/Translate';
import useBaseUrl from '@docusaurus/useBaseUrl';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Icon from '@site/src/components/Icon';
import styles from './index.module.css';

const FEATURES = [
  {icon: 'grid', title: translate({id: 'home.f.grid.t', message: 'Grids per monitor'}),
   text: translate({id: 'home.f.grid.d', message: 'Draggable grid lines, spans and nested subgrids – row 1 at 50:50, row 2 at 75:25, whatever your screens need.'})},
  {icon: 'layers', title: translate({id: 'home.f.profiles.t', message: 'Profiles & stacks'}),
   text: translate({id: 'home.f.profiles.d', message: 'Pin characters to slots, fill the rest automatically, stack clients on one spot and switch layouts with a hotkey.'})},
  {icon: 'wand', title: translate({id: 'home.f.auto.t', message: 'Auto placement'}),
   text: translate({id: 'home.f.auto.d', message: 'Log in ten clients at once – each one lands in its slot as soon as it appears.'})},
  {icon: 'zones', title: translate({id: 'home.f.zones.t', message: 'Window zones'}),
   text: translate({id: 'home.f.zones.d', message: 'Keep slots free for a browser, RIFT or your editor, or catch every new window in one place.'})},
  {icon: 'keyboard', title: translate({id: 'home.f.hotkeys.t', message: 'Global hotkeys'}),
   text: translate({id: 'home.f.hotkeys.d', message: 'Next/previous layout, cycle the active stack, one hotkey per stack – registered directly in KWin.'})},
  {icon: 'preview', title: translate({id: 'home.f.previews.t', message: 'Live previews'}), badge: true,
   text: translate({id: 'home.f.previews.d', message: 'Thumbnails like EVE-O Preview, rendered by KWin itself – no screen capture.'})},
  {icon: 'brush', title: translate({id: 'home.f.titlebars.t', message: 'Title bars & separators'}),
   text: translate({id: 'home.f.titlebars.d', message: 'Hide title bars for more game, thin separator lines only where two clients meet.'})},
  {icon: 'lock', title: translate({id: 'home.f.lock.t', message: 'Lock in place'}),
   text: translate({id: 'home.f.lock.d', message: 'Locked windows snap back when they get moved, resized or maximized by accident.'})},
];

function Hero() {
  const {i18n} = useDocusaurusContext();
  const lang = i18n.currentLocale === 'de' ? 'de' : 'en';
  return (
    <header className={styles.hero}>
      <div className={clsx('container', styles.heroInner)}>
        <div className={styles.heroText}>
          <img className={styles.logo} src={useBaseUrl('/img/logo.svg')} alt="" />
          <h1 className={styles.title}>FleetCommander</h1>
          <p className={styles.claim}><Translate id="home.claim">Every client in its place.</Translate></p>
          <p className={styles.lead}>
            <Translate id="home.lead">
              A grid window manager for EVE Online multiboxing on KDE Plasma – Wayland and X11. Profiles,
              stacks, hotkeys and a drag &amp; drop editor in your browser.
            </Translate>
          </p>
          <div className={styles.buttons}>
            <Link className="button button--primary button--lg" to="/docs/installation">
              <Translate id="home.cta.start">Get started</Translate>
            </Link>
            <Link className={clsx('button button--lg', styles.ghost)} to="/docs/">
              <Translate id="home.cta.docs">Documentation</Translate>
            </Link>
          </div>
          <ul className={styles.chips}>
            <li>KDE Plasma 6</li>
            <li>Wayland &amp; X11</li>
            <li>GPL-3.0</li>
            <li><Translate id="home.chip.input">No input to clients</Translate></li>
          </ul>
        </div>
        <div className={styles.shot}>
          <img data-zoom src={useBaseUrl(`/img/screenshots/layout-${lang}.png`)}
               alt={translate({id: 'home.shot.alt', message: 'The FleetCommander layout editor'})} />
        </div>
      </div>
    </header>
  );
}

function Features() {
  return (
    <section className={styles.section}>
      <div className="container">
        <h2 className={styles.h2}><Translate id="home.features.title">Built for multiboxing</Translate></h2>
        <div className={styles.grid}>
          {FEATURES.map((f) => (
            <div key={f.icon} className={styles.card}>
              <Icon name={f.icon} className={styles.cardIcon} />
              <h3>
                {f.title}
                {f.badge && <span className={styles.badge}><Translate id="home.badge.experimental">experimental</Translate></span>}
              </h3>
              <p>{f.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function NotJustEve() {
  const {i18n} = useDocusaurusContext();
  const lang = i18n.currentLocale === 'de' ? 'de' : 'en';
  return (
    <section className={clsx(styles.section, styles.alt)}>
      <div className={clsx('container', styles.split)}>
        <div>
          <Icon name="code" size={36} className={styles.cardIcon} />
          <h2 className={styles.h2Left}><Translate id="home.notjust.title">Not just for EVE</Translate></h2>
          <p>
            <Translate id="home.notjust.p1">
              Window zones work with any window, so fcwm is also a general grid tiler for KDE Plasma.
            </Translate>
          </p>
          <p>
            <Translate id="home.notjust.p2">
              I use it at work to arrange my development environment: IDE, terminals, browser and chat each get
              a fixed spot, and a hotkey switches between layouts.
            </Translate>
          </p>
          <Link to="/docs/window-zones"><Translate id="home.notjust.link">Read about window zones →</Translate></Link>
        </div>
        <div className={styles.shot}>
          <img data-zoom src={useBaseUrl(`/img/screenshots/cell-menu-${lang}.png`)}
               alt={translate({id: 'home.shot2.alt', message: 'The slot menu with window zone options'})} />
        </div>
      </div>
    </section>
  );
}

function Install() {
  return (
    <section className={styles.section}>
      <div className={clsx('container', styles.split)}>
        <div>
          <Icon name="terminal" size={36} className={styles.cardIcon} />
          <h2 className={styles.h2Left}><Translate id="home.install.title">Up and running in a minute</Translate></h2>
          <p>
            <Translate id="home.install.p">
              Build the Arch package, create a starter config and enable the user service. Packages for Debian,
              Fedora and a generic installer are included as well.
            </Translate>
          </p>
          <Link to="/docs/installation"><Translate id="home.install.link">All installation options →</Translate></Link>
        </div>
        <CodeBlock language="bash">{`git clone https://github.com/jfschubert/FleetCommander.git
cd FleetCommander/packaging/arch
makepkg -si
fcwm init
systemctl --user enable --now fcwm
fcwm open`}</CodeBlock>
      </div>
    </section>
  );
}

function FairPlay() {
  return (
    <section className={clsx(styles.section, styles.alt)}>
      <div className={clsx('container', styles.fair)}>
        <Icon name="shield" size={40} className={styles.cardIcon} />
        <div>
          <h2 className={styles.h2Left}><Translate id="home.fair.title">Only windows, never input</Translate></h2>
          <p>
            <Translate id="home.fair.p">
              fcwm arranges, switches and previews windows through the desktop's window manager. It never reads
              game memory and never sends keystrokes or clicks to game clients – the same category of tool as
              EVE-O Preview.
            </Translate>
          </p>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <Layout
      title={translate({id: 'home.meta.title', message: 'Window manager for EVE Online on KDE Plasma'})}
      description={translate({id: 'home.meta.desc', message: 'FleetCommander arranges EVE Online clients (and any other window) in per-monitor grids on KDE Plasma.'})}>
      <Hero />
      <main>
        <Features />
        <NotJustEve />
        <Install />
        <FairPlay />
      </main>
    </Layout>
  );
}
