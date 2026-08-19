import { Nav } from './components/Nav'
import { Hero } from './components/Hero'
import { Projects } from './components/Projects'
import { About } from './components/About'
import { Contact } from './components/Contact'
import { ScrollProgress } from './components/ScrollProgress'

export default function App() {
  return (
    <>
      <ScrollProgress />
      <Nav />
      <main>
        <Hero />
        <Projects />
        <About />
        <Contact />
      </main>
      <footer className="border-t border-white/5 px-6 py-10">
        <div className="mx-auto flex max-w-5xl flex-col gap-2 text-sm text-white/35 sm:flex-row sm:justify-between">
          <span>© {new Date().getFullYear()} Portfolio</span>
          <span>Built with React, Vite, and Framer Motion</span>
        </div>
      </footer>
    </>
  )
}
