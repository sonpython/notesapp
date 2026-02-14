import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/test/test-utils'
import { TodoItem } from './todo-item'
import type { Todo } from '@/lib/types'

describe('TodoItem', () => {
  const baseTodo: Todo = {
    id: '1',
    user_id: 'user1',
    title: 'Test Todo',
    description: null,
    is_completed: false,
    completed_at: null,
    deadline: null,
    parent_id: null,
    note_id: null,
    priority: 0,
    sort_order: 0,
    reminder_at: null,
    reminder_sent: false,
    recurrence_type: null,
    recurrence_interval: null,
    recurrence_days: null,
    recurrence_end_date: null,
    recurrence_parent_id: null,
    created_at: '2026-02-15T00:00:00Z',
    updated_at: '2026-02-15T00:00:00Z',
    tags: [],
  }

  it('should render todo title', () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    expect(screen.getByText('Test Todo')).toBeInTheDocument()
  })

  it('should show completion checkbox', () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const checkbox = screen.getByRole('button', { name: /mark complete/i })
    expect(checkbox).toBeInTheDocument()
  })

  it('should call onToggle when checkbox clicked', () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const checkbox = screen.getByRole('button', { name: /mark complete/i })
    fireEvent.click(checkbox)

    expect(onToggle).toHaveBeenCalledWith('1')
  })

  it('should show completed state', () => {
    const completedTodo = { ...baseTodo, is_completed: true }
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={completedTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    expect(screen.getByRole('button', { name: /mark incomplete/i })).toBeInTheDocument()
    const title = screen.getByText('Test Todo')
    expect(title).toHaveClass('line-through')
  })

  it('should edit title on double click', async () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const title = screen.getByText('Test Todo')
    fireEvent.doubleClick(title)

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Todo')).toBeInTheDocument()
    })
  })

  it('should commit edit on blur', async () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const title = screen.getByText('Test Todo')
    fireEvent.doubleClick(title)

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Todo')).toBeInTheDocument()
    })

    const input = screen.getByDisplayValue('Test Todo')
    fireEvent.change(input, { target: { value: 'Updated Todo' } })
    fireEvent.blur(input)

    expect(onUpdate).toHaveBeenCalledWith('1', { title: 'Updated Todo' })
  })

  it('should commit edit on Enter key', async () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const title = screen.getByText('Test Todo')
    fireEvent.doubleClick(title)

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Todo')).toBeInTheDocument()
    })

    const input = screen.getByDisplayValue('Test Todo')
    fireEvent.change(input, { target: { value: 'Updated Todo' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(onUpdate).toHaveBeenCalledWith('1', { title: 'Updated Todo' })
  })

  it('should not commit edit if title unchanged', async () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const title = screen.getByText('Test Todo')
    fireEvent.doubleClick(title)

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Todo')).toBeInTheDocument()
    })

    const input = screen.getByDisplayValue('Test Todo')
    fireEvent.blur(input)

    expect(onUpdate).not.toHaveBeenCalled()
  })

  it('should cancel edit on Escape key', async () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const title = screen.getByText('Test Todo')
    fireEvent.doubleClick(title)

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Todo')).toBeInTheDocument()
    })

    const input = screen.getByDisplayValue('Test Todo')
    fireEvent.change(input, { target: { value: 'Updated Todo' } })
    fireEvent.keyDown(input, { key: 'Escape' })

    expect(onUpdate).not.toHaveBeenCalled()
  })

  it('should show priority dot', () => {
    const priorityTodo = { ...baseTodo, priority: 1 }
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    const { container } = render(
      <TodoItem
        todo={priorityTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const dot = container.querySelector('.bg-blue-500')
    expect(dot).toBeInTheDocument()
  })

  it('should show deadline', () => {
    const deadlineTodo = {
      ...baseTodo,
      deadline: '2026-03-15T10:00:00Z',
    }
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={deadlineTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    expect(screen.getByText(/mar 15/i)).toBeInTheDocument()
  })

  it('should show reminder indicator', () => {
    const reminderTodo = {
      ...baseTodo,
      reminder_at: '2026-02-15T09:00:00Z',
    }
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    const { container } = render(
      <TodoItem
        todo={reminderTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const reminderSpan = container.querySelector('span[title="Reminder set"]')
    expect(reminderSpan).toBeInTheDocument()
  })

  it('should call onDelete when delete button clicked', () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const deleteBtn = screen.getByRole('button', { name: /delete todo/i })
    fireEvent.click(deleteBtn)

    expect(onDelete).toHaveBeenCalledWith('1')
  })

  it('should expand and collapse children', () => {
    const childTodo: Todo = { ...baseTodo, id: '2', title: 'Subtask', parent_id: '1' }
    const parentTodo: Todo = { ...baseTodo, children: [childTodo] }
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    const { rerender } = render(
      <TodoItem
        todo={parentTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    const expandBtn = screen.getByRole('button', { name: /expand/i })
    fireEvent.click(expandBtn)

    rerender(
      <TodoItem
        todo={parentTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    expect(screen.getByText('Subtask')).toBeInTheDocument()
  })

  it('should apply depth padding', () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    const { container } = render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={2}
      />,
    )

    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.style.paddingLeft).toBe('48px')
  })

  it('should show add subtask button', () => {
    const onToggle = vi.fn()
    const onUpdate = vi.fn()
    const onDelete = vi.fn()

    render(
      <TodoItem
        todo={baseTodo}
        onToggle={onToggle}
        onUpdate={onUpdate}
        onDelete={onDelete}
        depth={0}
      />,
    )

    expect(screen.getByRole('button', { name: /add subtask/i })).toBeInTheDocument()
  })
})
