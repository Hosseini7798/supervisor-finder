use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::{AppHandle, Manager, State};

struct BackendProcess {
    child: Mutex<Option<Child>>,
}

impl Default for BackendProcess {
    fn default() -> Self {
        Self {
            child: Mutex::new(None),
        }
    }
}

fn resolve_backend_root(app: &AppHandle) -> PathBuf {
    let dev_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
    if dev_root.join("api").exists() && dev_root.join("src").exists() {
        return dev_root;
    }

    if let Ok(resource_dir) = app.path().resource_dir() {
        if resource_dir.join("api").exists() && resource_dir.join("src").exists() {
            return resource_dir;
        }
    }

    dev_root
}

fn is_child_running(child: &mut Child) -> bool {
    match child.try_wait() {
        Ok(Some(_)) => false,
        Ok(None) => true,
        Err(_) => false,
    }
}

fn spawn_backend(app: &AppHandle) -> Result<Child, String> {
    let backend_root = resolve_backend_root(app);
    let path_sep = if cfg!(windows) { ';' } else { ':' };
    let python_path = format!(
        "{}{}{}",
        backend_root.join("src").display(),
        path_sep,
        backend_root.display()
    );

    let args = [
        "-m",
        "uvicorn",
        "api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--log-level",
        "warning",
    ];

    let mut python = Command::new("python");
    python
        .args(args)
        .current_dir(&backend_root)
        .env("PYTHONPATH", &python_path)
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    match python.spawn() {
        Ok(child) => Ok(child),
        Err(primary_error) => {
            if cfg!(windows) {
                let mut py_launcher = Command::new("py");
                py_launcher
                    .arg("-3")
                    .args(args)
                    .current_dir(&backend_root)
                    .env("PYTHONPATH", &python_path)
                    .stdout(Stdio::null())
                    .stderr(Stdio::null());

                py_launcher.spawn().map_err(|fallback_error| {
                    format!(
                        "Failed to start backend with python ({primary_error}) and py -3 ({fallback_error})"
                    )
                })
            } else {
                Err(format!("Failed to start backend: {primary_error}"))
            }
        }
    }
}

fn start_backend_internal(app: &AppHandle, state: &BackendProcess) -> Result<bool, String> {
    let mut guard = state
        .child
        .lock()
        .map_err(|_| "Backend lock poisoned".to_string())?;

    if let Some(child) = guard.as_mut() {
        if is_child_running(child) {
            return Ok(false);
        }
        *guard = None;
    }

    let child = spawn_backend(app)?;
    *guard = Some(child);
    Ok(true)
}

fn stop_backend_internal(state: &BackendProcess) -> Result<bool, String> {
    let mut guard = state
        .child
        .lock()
        .map_err(|_| "Backend lock poisoned".to_string())?;

    let Some(mut child) = guard.take() else {
        return Ok(false);
    };

    let _ = child.kill();
    let _ = child.wait();
    Ok(true)
}

fn backend_running_internal(state: &BackendProcess) -> Result<bool, String> {
    let mut guard = state
        .child
        .lock()
        .map_err(|_| "Backend lock poisoned".to_string())?;

    let Some(child) = guard.as_mut() else {
        return Ok(false);
    };

    if is_child_running(child) {
        Ok(true)
    } else {
        *guard = None;
        Ok(false)
    }
}

#[tauri::command]
fn start_backend(app: AppHandle, state: State<'_, BackendProcess>) -> Result<bool, String> {
    start_backend_internal(&app, &state)
}

#[tauri::command]
fn stop_backend(state: State<'_, BackendProcess>) -> Result<bool, String> {
    stop_backend_internal(&state)
}

#[tauri::command]
fn backend_process_running(state: State<'_, BackendProcess>) -> Result<bool, String> {
    backend_running_internal(&state)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .manage(BackendProcess::default())
        .setup(|app| {
            let state = app.state::<BackendProcess>();
            if let Err(err) = start_backend_internal(&app.handle(), &state) {
                eprintln!("Backend auto-start failed: {err}");
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            start_backend,
            stop_backend,
            backend_process_running
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if let tauri::RunEvent::Exit = event {
            let state = app_handle.state::<BackendProcess>();
            let _ = stop_backend_internal(&state);
        }
    });
}
