import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import LandingPage from './LandingPage'

describe('LandingPage', () => {
  it('presents the learner-first product and an authentication entry point', () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: /learn the language.*live the meaning/i })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /start learning|meet your tutor/i }).length).toBeGreaterThan(0)
  })

  it('preserves the selected language for registration', () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>)
    expect(screen.getAllByRole('link', { name: /GermanConfident grammar/i }).every(
      (link) => link.getAttribute('href') === '/auth?language=de'
    )).toBe(true)
  })
})
