<template>
  <div class="min-h-screen bg-bg-base text-text-primary">
    <div class="mx-auto w-full max-w-[1600px] grid grid-cols-1 md:grid-cols-[260px_1fr] gap-4 p-4 md:p-6">
      <aside class="sci-panel min-h-[200px] p-4">
        <div class="text-sm text-text-muted tracking-[0.08em] uppercase">Admin Console</div>
      </aside>
      <main class="sci-panel min-h-[70vh] p-4 md:p-6">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped></style>
