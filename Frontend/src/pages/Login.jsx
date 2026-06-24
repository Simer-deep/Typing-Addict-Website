import { useState } from "react";

function Login({ checkingSession, handleLogin, handleLogout, user }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submitLogin(event) {
    event.preventDefault();
    setMessage("");
    setSubmitting(true);

    const result = await handleLogin(username, password);

    setSubmitting(false);
    setMessage(result.message);

    if (result.ok) {
      setPassword("");
    }
  }

  return (
    <main className="login-page">
      <div className="race-lines" aria-hidden="true" />

      <div className="login-layout">
        <section className="brand-panel">
          <p className="brand-mark">TA</p>
          <p className="eyebrow">Typing Addict</p>
          <h1>Type fast.<br />Bet smart.</h1>
          <p className="tagline">Head-to-head typing races with real stakes.</p>
        </section>

        <section className="login-card" aria-labelledby="login-title">
          {checkingSession ? (
            <p className="session-status" role="status">Checking session...</p>
          ) : user ? (
            <div className="signed-in">
              <p className="status-kicker">Signed in</p>
              <h2 id="login-title">{user.username}</h2>
              <button className="secondary-button" type="button" onClick={handleLogout}>
                Sign out
              </button>
            </div>
          ) : (
            <>
              <p className="status-kicker">Welcome back</p>
              <h2 id="login-title">Sign in</h2>

              <form onSubmit={submitLogin}>
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  autoFocus
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                />

                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />

                <button className="login-button" type="submit" disabled={submitting}>
                  {submitting ? "Signing in..." : "Enter the race floor"}
                </button>

                <p className="form-message" role="status" aria-live="polite">
                  {message}
                </p>
              </form>
            </>
          )}
        </section>
      </div>

      <p className="responsible-note">18+ only. Play responsibly.</p>
    </main>
  );
}

export default Login;
