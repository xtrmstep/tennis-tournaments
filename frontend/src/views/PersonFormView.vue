<template>
  <div style="max-width: 500px;">
    <h2>Add Person</h2>
    <form @submit.prevent="handleSubmit" enctype="multipart/form-data">
      <div style="margin-bottom: 1rem;">
        <label>Name *</label><br />
        <input v-model="name" type="text" required style="width: 100%; padding: 0.5rem;" />
        <p v-if="nameError" style="color: red; font-size: 0.85rem;">{{ nameError }}</p>
      </div>
      <div style="margin-bottom: 1rem;">
        <label>Skill (optional)</label><br />
        <input v-model="skill" type="text" style="width: 100%; padding: 0.5rem;" />
      </div>
      <div style="margin-bottom: 1rem;">
        <label>Photo (optional)</label><br />
        <input type="file" accept=".jpg,.jpeg,.png,.gif" @change="onFileChange" />
      </div>
      <p v-if="error" style="color: red;">{{ error }}</p>
      <div style="display: flex; gap: 0.5rem;">
        <button type="submit" :disabled="loading">{{ loading ? 'Saving…' : 'Save' }}</button>
        <RouterLink to="/people"><button type="button">Cancel</button></RouterLink>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { createPerson } from '../services/api'

const router = useRouter()
const name = ref('')
const skill = ref('')
const photoFile = ref(null)
const nameError = ref('')
const error = ref('')
const loading = ref(false)

function onFileChange(event) {
  photoFile.value = event.target.files[0] || null
}

async function handleSubmit() {
  nameError.value = ''
  error.value = ''

  if (!name.value.trim()) {
    nameError.value = 'Name is required'
    return
  }

  const formData = new FormData()
  formData.append('name', name.value.trim())
  if (skill.value.trim()) formData.append('skill', skill.value.trim())
  if (photoFile.value) formData.append('photo', photoFile.value)

  loading.value = true
  try {
    await createPerson(formData)
    router.push('/people')
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to create person'
  } finally {
    loading.value = false
  }
}
</script>
