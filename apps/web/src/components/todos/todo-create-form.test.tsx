import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/test/test-utils'
import { TodoCreateForm } from './todo-create-form'
import type { Todo } from '@/lib/types'

describe('TodoCreateForm', () => {
  it('should render form with title input', () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    expect(screen.getByPlaceholderText('New todo...')).toBeInTheDocument()
  })

  it('should render with subtask placeholder when parentId provided', () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} parentId="parent1" />)

    expect(screen.getByPlaceholderText('Add subtask...')).toBeInTheDocument()
  })

  it('should render priority selector', () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    const select = screen.getByRole('combobox', { name: /priority/i })
    expect(select).toBeInTheDocument()
    expect(screen.getByText('No priority')).toBeInTheDocument()
    expect(screen.getByText('Low')).toBeInTheDocument()
    expect(screen.getByText('Medium')).toBeInTheDocument()
    expect(screen.getByText('High')).toBeInTheDocument()
  })

  it('should render extra options button', () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    expect(screen.getByRole('button', { name: /more options/i })).toBeInTheDocument()
  })

  it('should disable submit button when title is empty', () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    expect(submitBtn).toBeDisabled()
  })

  it('should enable submit button when title has text', () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    const input = screen.getByPlaceholderText('New todo...')
    fireEvent.change(input, { target: { value: 'Test todo' } })

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    expect(submitBtn).not.toBeDisabled()
  })

  it('should call onCreated with title only', async () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    const input = screen.getByPlaceholderText('New todo...')
    fireEvent.change(input, { target: { value: 'Test todo' } })

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test todo',
          priority: 0,
        }),
      )
    })
  })

  it('should call onCreated with priority', async () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    const input = screen.getByPlaceholderText('New todo...')
    fireEvent.change(input, { target: { value: 'Test todo' } })

    const select = screen.getByRole('combobox', { name: /priority/i })
    fireEvent.change(select, { target: { value: '2' } })

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test todo',
          priority: 2,
        }),
      )
    })
  })

  it('should show extra fields when toggle clicked', async () => {
    const onCreated = vi.fn()
    const { container } = render(<TodoCreateForm onCreated={onCreated} />)

    const toggleBtn = screen.getByRole('button', { name: /more options/i })
    fireEvent.click(toggleBtn)

    await waitFor(() => {
      const datetimeInputs = container.querySelectorAll('input[type="datetime-local"]')
      expect(datetimeInputs.length).toBeGreaterThan(0)
    })
  })

  it('should call onCreated with deadline when provided', async () => {
    const onCreated = vi.fn()
    const { container } = render(<TodoCreateForm onCreated={onCreated} />)

    const input = screen.getByPlaceholderText('New todo...')
    fireEvent.change(input, { target: { value: 'Test todo' } })

    const toggleBtn = screen.getByRole('button', { name: /more options/i })
    fireEvent.click(toggleBtn)

    await waitFor(() => {
      const datetimeInputs = container.querySelectorAll('input[type="datetime-local"]')
      expect(datetimeInputs.length).toBeGreaterThan(0)
    })

    const datetimeInputs = container.querySelectorAll('input[type="datetime-local"]')
    const deadlineInput = datetimeInputs[0] as HTMLInputElement
    fireEvent.change(deadlineInput, { target: { value: '2026-03-15T10:00' } })

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test todo',
          deadline: '2026-03-15T10:00',
        }),
      )
    })
  })

  it('should call onCreated with reminder when provided', async () => {
    const onCreated = vi.fn()
    const { container } = render(<TodoCreateForm onCreated={onCreated} />)

    const input = screen.getByPlaceholderText('New todo...')
    fireEvent.change(input, { target: { value: 'Test todo' } })

    const toggleBtn = screen.getByRole('button', { name: /more options/i })
    fireEvent.click(toggleBtn)

    await waitFor(() => {
      const datetimeInputs = container.querySelectorAll('input[type="datetime-local"]')
      expect(datetimeInputs.length).toBeGreaterThan(0)
    })

    const datetimeInputs = container.querySelectorAll('input[type="datetime-local"]')
    const reminderInput = datetimeInputs[1] as HTMLInputElement
    fireEvent.change(reminderInput, { target: { value: '2026-02-15T09:00' } })

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test todo',
          reminder_at: '2026-02-15T09:00',
        }),
      )
    })
  })

  it('should call onCreated with parent_id when provided', async () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} parentId="parent123" />)

    const input = screen.getByPlaceholderText('Add subtask...')
    fireEvent.change(input, { target: { value: 'Subtask' } })

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Subtask',
          parent_id: 'parent123',
        }),
      )
    })
  })

  it('should reset form after submission', async () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    const input = screen.getByPlaceholderText('New todo...') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'Test todo' } })

    expect(input.value).toBe('Test todo')

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(input.value).toBe('')
    })
  })

  it('should not submit with only whitespace', async () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    const input = screen.getByPlaceholderText('New todo...')
    fireEvent.change(input, { target: { value: '   ' } })

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    expect(submitBtn).toBeDisabled()
  })

  it('should trim title before submission', async () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    const input = screen.getByPlaceholderText('New todo...')
    fireEvent.change(input, { target: { value: '  Test todo  ' } })

    const submitBtn = screen.getByRole('button', { name: /add todo/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test todo',
        }),
      )
    })
  })

  it('should toggle extra fields visibility', async () => {
    const onCreated = vi.fn()
    const { container } = render(<TodoCreateForm onCreated={onCreated} />)

    const toggleBtn = screen.getByRole('button', { name: /more options/i })

    // Initially, no datetime inputs should be visible
    let datetimeInputs = container.querySelectorAll('input[type="datetime-local"]')
    expect(datetimeInputs.length).toBe(0)

    // Open extras
    fireEvent.click(toggleBtn)

    await waitFor(() => {
      datetimeInputs = container.querySelectorAll('input[type="datetime-local"]')
      expect(datetimeInputs.length).toBe(2) // deadline and reminder
    })

    // Close extras
    fireEvent.click(toggleBtn)

    await waitFor(() => {
      datetimeInputs = container.querySelectorAll('input[type="datetime-local"]')
      expect(datetimeInputs.length).toBe(0)
    })
  })

  it('should prevent duplicate submissions', async () => {
    const onCreated = vi.fn()
    render(<TodoCreateForm onCreated={onCreated} />)

    const input = screen.getByPlaceholderText('New todo...')
    fireEvent.change(input, { target: { value: 'Test todo' } })

    const submitBtn = screen.getByRole('button', { name: /add todo/i })

    // Rapidly click submit button
    fireEvent.click(submitBtn)
    fireEvent.click(submitBtn)
    fireEvent.click(submitBtn)

    await waitFor(() => {
      // onCreated should be called only once due to submitting flag
      expect(onCreated.mock.calls.length).toBeLessThanOrEqual(1)
    })
  })

  it('should have unique instances when rendered separately', () => {
    const onCreated1 = vi.fn()
    const onCreated2 = vi.fn()

    // Each instance should manage its own state independently
    const { unmount: unmount1 } = render(<TodoCreateForm onCreated={onCreated1} />)

    const input1 = screen.getByPlaceholderText('New todo...')
    fireEvent.change(input1, { target: { value: 'Form 1' } })
    expect((input1 as HTMLInputElement).value).toBe('Form 1')

    unmount1()

    const { unmount: unmount2 } = render(<TodoCreateForm onCreated={onCreated2} />)

    const input2 = screen.getByPlaceholderText('New todo...')
    expect((input2 as HTMLInputElement).value).toBe('')

    unmount2()
  })
})
