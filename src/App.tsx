import { useEffect } from 'react';
import { useTheme } from './contexts/ThemeContext';
import { Header } from './components/Header/Header';
import { Hero } from './components/Hero/Hero';
import { Editorial } from './components/Editorial/Editorial';
import { Statistics } from './components/Statistics/Statistics';
import { Contents } from './components/Contents/Contents';
import { Volumes } from './components/Volumes/Volumes';
import { IsaacCathedral } from './components/IsaacCathedral/IsaacCathedral';
import { Audience } from './components/Audience/Audience';
import { AccessSteps } from './components/AccessSteps/AccessSteps';
import { RequestForm } from './components/RequestForm/RequestForm';
import { FAQ } from './components/FAQ/FAQ';
import { Footer } from './components/Footer/Footer';
import { buildApiUrl } from './config/api';

function App() {
  const { theme } = useTheme();

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const sentKey = 'antology_site_visit_sent';
    const sessionKey = 'antology_site_visit_session_id';

    if (window.sessionStorage.getItem(sentKey) === '1') {
      return;
    }

    const sessionId =
      window.sessionStorage.getItem(sessionKey) ||
      (typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `visit-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`);

    window.sessionStorage.setItem(sessionKey, sessionId);
    window.sessionStorage.setItem(sentKey, '1');

    void fetch(buildApiUrl('/api/site-visit'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      keepalive: true,
      body: JSON.stringify({
        session_id: sessionId,
        path: window.location.pathname,
        referrer: document.referrer || null,
      }),
    }).catch(() => {
      window.sessionStorage.removeItem(sentKey);
    });
  }, []);

  return (
    <div className={`min-h-screen overflow-x-hidden transition-colors duration-500 ${
      theme === 'dark' ? 'dark' : ''
    }`} id="top">
      <Header />
      <main>
        <Hero />
        <Editorial />
        <Statistics />
        <Contents />
        <Volumes />
        <IsaacCathedral />
        <Audience />
        <AccessSteps />
        <RequestForm />
        <FAQ />
      </main>
      <Footer />
    </div>
  );
}

export default App;
