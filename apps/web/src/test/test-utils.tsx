import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'

/**
 * Custom render function that wraps components with necessary providers.
 * Can be extended with Router, Theme, Auth contexts as needed.
 */
function CustomRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <>{children}</>
  }

  return render(ui, { wrapper: Wrapper, ...options })
}

export * from '@testing-library/react'
export { CustomRender as render }
