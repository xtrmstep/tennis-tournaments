<template>
  <div style="position: relative; display: flex; gap: 1rem;">
    <!-- Main user table -->
    <div style="flex: 1; min-width: 0;">
      <h2>User Management</h2>

      <p v-if="loading">Loading…</p>
      <p v-if="error" style="color: red;">{{ error }}</p>
      <p v-if="successMsg" style="color: green;">{{ successMsg }}</p>

      <table v-if="!loading && users.length" style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
        <thead>
          <tr>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Email</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Full Name</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Username</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Skill</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Gender</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Profile</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Status</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Last Updated</th>
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="user in users"
            :key="user.id"
            :style="{ background: selectedUser && selectedUser.id === user.id ? '#e8f5e9' : '', cursor: 'pointer' }"
            @click="selectUser(user)"
          >
            <td style="padding: 0.5rem;">{{ user.email }}</td>
            <td style="padding: 0.5rem;">{{ user.full_name || '—' }}</td>
            <td style="padding: 0.5rem;">{{ user.username || '—' }}</td>
            <td style="padding: 0.5rem;">{{ user.skill_level ?? '—' }}</td>
            <td style="padding: 0.5rem;">{{ user.gender || '—' }}</td>
            <td style="padding: 0.5rem;">{{ user.profile_complete ? 'Complete' : 'Incomplete' }}</td>
            <td style="padding: 0.5rem;">
              <span :style="{ color: user.is_active ? 'green' : 'red' }">
                {{ user.is_active ? 'Active' : 'Disabled' }}
              </span>
            </td>
            <td style="padding: 0.5rem;">{{ user.updated_at ? new Date(user.updated_at).toLocaleString() : '—' }}</td>
            <td style="padding: 0.5rem;" @click.stop>
              <button
                v-if="user.is_active && !user.is_admin"
                style="margin-right: 0.25rem;"
                @click="confirmToggle(user)"
              >Disable</button>
              <button
                v-if="!user.is_active"
                style="margin-right: 0.25rem;"
                @click="confirmToggle(user)"
              >Enable</button>
              <button
                v-if="!user.is_admin"
                style="color: red;"
                @click="confirmDelete(user)"
              >Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else-if="!loading">No users found.</p>
    </div>

    <!-- Sidebar -->
    <transition name="slide">
      <aside
        v-if="selectedUser"
        style="width: 320px; border-left: 2px solid #2c5f2e; padding: 1rem; background: #f9f9f9; position: sticky; top: 0; max-height: 100vh; overflow-y: auto;"
      >
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="margin: 0;">{{ selectedUser.full_name || selectedUser.email }}</h3>
          <button @click="selectedUser = null" style="border: none; background: none; font-size: 1.2rem; cursor: pointer;">✕</button>
        </div>
        <p style="margin-top: 0.5rem; color: #555; font-size: 0.9rem;">{{ selectedUser.email }}</p>
        <hr />
        <h4>Events</h4>
        <p style="color: #888; font-style: italic;">Events are not yet implemented.</p>
      </aside>
    </transition>

    <!-- Disable/Enable confirmation modal -->
    <div
      v-if="userToToggle"
      style="position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100;"
      @click.self="userToToggle = null"
    >
      <div style="background: white; padding: 2rem; border-radius: 8px; max-width: 360px; width: 100%;">
        <h3>{{ userToToggle.is_active ? 'Disable' : 'Enable' }} user?</h3>
        <p>
          <strong>{{ userToToggle.email }}</strong> will be
          {{ userToToggle.is_active ? 'disabled and will no longer be able to log in' : 're-enabled and will be able to log in again' }}.
        </p>
        <div style="display: flex; gap: 1rem; justify-content: flex-end;">
          <button @click="userToToggle = null">Cancel</button>
          <button
            :style="{ background: userToToggle.is_active ? '#d32f2f' : '#2c5f2e', color: 'white', border: 'none', padding: '0.4rem 1rem', cursor: 'pointer', borderRadius: '4px' }"
            @click="doToggle"
          >{{ userToToggle.is_active ? 'Disable' : 'Enable' }}</button>
        </div>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div
      v-if="userToDelete"
      style="position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100;"
      @click.self="userToDelete = null"
    >
      <div style="background: white; padding: 2rem; border-radius: 8px; max-width: 360px; width: 100%;">
        <h3>Delete user?</h3>
        <p>All data for <strong>{{ userToDelete.email }}</strong> will be permanently removed.</p>
        <div style="display: flex; gap: 1rem; justify-content: flex-end;">
          <button @click="userToDelete = null">Cancel</button>
          <button style="background: red; color: white; border: none; padding: 0.4rem 1rem; cursor: pointer; border-radius: 4px;" @click="doDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminListUsers, adminPatchUser, adminDeleteUser } from '../services/api'

const users = ref([])
const loading = ref(false)
const error = ref('')
const successMsg = ref('')
const selectedUser = ref(null)
const userToDelete = ref(null)
const userToToggle = ref(null)

async function fetchUsers() {
  loading.value = true
  error.value = ''
  try {
    const res = await adminListUsers()
    users.value = res.data
  } catch {
    error.value = 'Failed to load users'
  } finally {
    loading.value = false
  }
}

onMounted(fetchUsers)

function selectUser(user) {
  selectedUser.value = selectedUser.value?.id === user.id ? null : user
}

function confirmToggle(user) {
  userToToggle.value = user
}

async function doToggle() {
  if (!userToToggle.value) return
  error.value = ''
  successMsg.value = ''
  const user = userToToggle.value
  userToToggle.value = null
  try {
    const res = await adminPatchUser(user.id, { is_active: !user.is_active })
    const idx = users.value.findIndex(u => u.id === user.id)
    if (idx !== -1) users.value[idx] = res.data
    if (selectedUser.value?.id === user.id) selectedUser.value = res.data
    successMsg.value = `User ${res.data.is_active ? 'enabled' : 'disabled'}.`
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to update user'
  }
}

function confirmDelete(user) {
  userToDelete.value = user
}

async function doDelete() {
  if (!userToDelete.value) return
  error.value = ''
  successMsg.value = ''
  try {
    await adminDeleteUser(userToDelete.value.id)
    users.value = users.value.filter(u => u.id !== userToDelete.value.id)
    if (selectedUser.value?.id === userToDelete.value.id) selectedUser.value = null
    successMsg.value = 'User deleted.'
    userToDelete.value = null
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to delete user'
    userToDelete.value = null
  }
}
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(40px);
  opacity: 0;
}
</style>
