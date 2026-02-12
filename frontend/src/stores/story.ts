import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { StoryNodeRead, StoryBook } from '@/types'

export const useStoryStore = defineStore('story', () => {
  // State
  const currentNode = ref<StoryNodeRead | null>(null)
  const currentBook = ref<StoryBook | null>(null)
  const isReading = ref<boolean>(false)
  const isWriting = ref<boolean>(false)

  // Actions
  const setCurrentNode = (node: StoryNodeRead) => {
    currentNode.value = node
  }

  const setCurrentBook = (book: StoryBook) => {
    currentBook.value = book
  }

  const clearCurrentNode = () => {
    currentNode.value = null
  }

  const clearCurrentBook = () => {
    currentBook.value = null
  }

  const setReadingState = (state: boolean) => {
    isReading.value = state
  }

  const setWritingState = (state: boolean) => {
    isWriting.value = state
  }

  return {
    currentNode,
    currentBook,
    isReading,
    isWriting,
    setCurrentNode,
    setCurrentBook,
    clearCurrentNode,
    clearCurrentBook,
    setReadingState,
    setWritingState,
  }
})