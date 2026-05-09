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
            <th style="text-align: left; padding: 0.5rem; border-bottom: 1px solid #ccc;">Role</th>
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
            <td style="padding: 0.5rem;" @click.stop>
              <select
                v-if="!user.is_admin"
                :value="user.is_moderator ? 'moderator' : 'user'"
                @change="confirmRoleChange(user, $event.target.value)"
                style="padding: 0.2rem;"
              >
                <option value="user">Regular User</option>
                <option value="moderator">Moderator</option>
              </select>
              <span v-else style="color: #888;">Admin</span>
            </td>
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

    <!-- Profile edit sidebar -->
    <transition name="slide">
      <aside
        v-if="selectedUser"
        style="width: 340px; border-left: 2px solid #2c5f2e; padding: 1rem; background: #f9f9f9; position: sticky; top: 0; max-height: 100vh; overflow-y: auto;"
      >
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="margin: 0;">Edit Profile</h3>
          <button @click="closeSidebar" style="border: none; background: none; font-size: 1.2rem; cursor: pointer;">✕</button>
        </div>
        <p style="margin-top: 0.25rem; color: #555; font-size: 0.85rem;">{{ selectedUser.email }}</p>
        <hr />
        <p v-if="sidebarError" style="color: red; font-size: 0.9rem;">{{ sidebarError }}</p>
        <p v-if="sidebarSuccess" style="color: green; font-size: 0.9rem;">{{ sidebarSuccess }}</p>
        <form @submit.prevent="saveProfile" style="display: flex; flex-direction: column; gap: 0.75rem;">
          <label style="font-size: 0.9rem;">
            Email
            <input v-model="editForm.email" type="email" required style="display: block; width: 100%; margin-top: 0.2rem; padding: 0.3rem;" />
          </label>
          <label style="font-size: 0.9rem;">
            Full Name
            <input v-model="editForm.full_name" type="text" required style="display: block; width: 100%; margin-top: 0.2rem; padding: 0.3rem;" />
          </label>
          <label style="font-size: 0.9rem;">
            Username
            <input v-model="editForm.username" type="text" required style="display: block; width: 100%; margin-top: 0.2rem; padding: 0.3rem;" />
          </label>
          <label style="font-size: 0.9rem;">
            Skill Level (0–10)
            <input v-model.number="editForm.skill_level" type="number" min="0" max="10" required style="display: block; width: 100%; margin-top: 0.2rem; padding: 0.3rem;" />
          </label>
          <label style="font-size: 0.9rem;">
            Gender
            <input v-model="editForm.gender" type="text" required style="display: block; width: 100%; margin-top: 0.2rem; padding: 0.3rem;" />
          </label>
          <button
            type="submit"
            :disabled="savingProfile"
            style="background: #2c5f2e; color: white; border: none; padding: 0.5rem 1rem; cursor: pointer; border-radius: 4px; margin-top: 0.5rem;"
          >{{ savingProfile ? 'Saving…' : 'Save' }}</button>
        </form>
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

    <!-- Role change confirmation modal -->
    <div
      v-if="roleChangeTarget"
      style="position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100;"
      @click.self="cancelRoleChange"
    >
      <div style="background: white; padding: 2rem; border-radius: 8px; max-width: 380px; width: 100%;">
        <h3>Change role?</h3>
        <p>
          Set <strong>{{ roleChangeTarget.user.email }}</strong> as
          <strong>{{ roleChangeTarget.newRole === 'moderator' ? 'Event Moderator' : 'Regular User' }}</strong>?
        </p>
        <div style="display: flex; gap: 1rem; justify-content: flex-end;">
          <button @click="cancelRoleChange">Cancel</button>
          <button
            style="background: #2c5f2e; color: white; border: none; padding: 0.4rem 1rem; cursor: pointer; border-radius: 4px;"
            @click="doRoleChange"
          >Confirm</button>
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
import { adminListUsers, adminPatchUser, adminUpdateUserProfile, adminDeleteUser } from '../services/api'

const users = ref([])
const loading = ref(false)
const error = ref('')
const successMsg = ref('')
const selectedUser = ref(null)
const userToDelete = ref(null)
const userToToggle = ref(null)
const roleChangeTarget = ref(null)

const editForm = ref({ email: '', full_name: '', username: '', skill_level: '', gender: '' })
const savingProfile = ref(false)
const sidebarError = ref('')
const sidebarSuccess = ref('')

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
  if (selectedUser.value?.id === user.id) {
    closeSidebar()
    return
  }
  selectedUser.value = user
  sidebarError.value = ''
  sidebarSuccess.value = ''
  editForm.value = {
    email: user.email,
    full_name: user.full_name || '',
    username: user.username || '',
    skill_level: user.skill_level ?? '',
    gender: user.gender || '',
  }
}

function closeSidebar() {
  selectedUser.value = null
  sidebarError.value = ''
  sidebarSuccess.value = ''
}

async function saveProfile() {
  if (!selectedUser.value) return
  savingProfile.value = true
  sidebarError.value = ''
  sidebarSuccess.value = ''
  try {
    const res = await adminUpdateUserProfile(selectedUser.value.id, {
      email: editForm.value.email,
      full_name: editForm.value.full_name,
      username: editForm.value.username,
      skill_level: Number(editForm.value.skill_level),
      gender: editForm.value.gender,
    })
    const idx = users.value.findIndex(u => u.id === selectedUser.value.id)
    if (idx !== -1) users.value[idx] = res.data
    selectedUser.value = res.data
    sidebarSuccess.value = 'Profile saved.'
  } catch (e) {
    sidebarError.value = e.response?.data?.error || 'Failed to save profile'
  } finally {
    savingProfile.value = false
  }
}

function confirmRoleChange(user, newRole) {
  roleChangeTarget.value = { user, newRole }
}

function cancelRoleChange() {
  roleChangeTarget.value = null
}

async function doRoleChange() {
  if (!roleChangeTarget.value) return
  const { user, newRole } = roleChangeTarget.value
  roleChangeTarget.value = null
  error.value = ''
  successMsg.value = ''
  try {
    const res = await adminPatchUser(user.id, { is_moderator: newRole === 'moderator' })
    const idx = users.value.findIndex(u => u.id === user.id)
    if (idx !== -1) users.value[idx] = res.data
    if (selectedUser.value?.id === user.id) selectedUser.value = res.data
    successMsg.value = `Role updated to ${newRole === 'moderator' ? 'Moderator' : 'Regular User'}.`
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to update role'
  }
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
    if (selectedUser.value?.id === userToDelete.value.id) closeSidebar()
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

