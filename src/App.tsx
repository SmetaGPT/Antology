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

function App() {
  const { theme } = useTheme();

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
