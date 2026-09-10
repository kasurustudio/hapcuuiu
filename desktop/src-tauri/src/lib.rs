//! Shell Tauri untuk Stock Analysis Platform.
//!
//! Menjalankan backend Python (dibundel PyInstaller, lihat
//! backend/desktop_entrypoint.py & backend/desktop.spec) sebagai sidecar
//! process di localhost, dan menutupnya bersih saat app di-quit — supaya
//! tidak ada proses backend yang "nyangkut" (orphan) setelah window ditutup.

use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Handle proses backend, disimpan di state Tauri supaya bisa di-kill
/// eksplisit saat app exit (lihat `RunEvent::Exit` di bawah).
struct BackendProcess(Mutex<Option<CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let shell = app.handle().shell();
            let sidecar_command = shell
                .sidecar("stockapp-backend")
                .expect("gagal menyiapkan sidecar stockapp-backend — pastikan binary sudah di-build (lihat backend/desktop.spec) dan terdaftar di tauri.conf.json bundle.externalBin");

            let (mut rx, child) = sidecar_command
                .spawn()
                .expect("gagal menjalankan sidecar backend");

            app.state::<BackendProcess>()
                .0
                .lock()
                .expect("lock BackendProcess")
                .replace(child);

            // Alirkan log stdout/stderr backend ke konsol Tauri — berguna
            // untuk debug lewat `tauri dev`, tidak terlihat user awam di
            // build release (window "windows_subsystem" tidak punya konsol).
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            println!("[backend] {}", String::from_utf8_lossy(&line));
                        }
                        CommandEvent::Stderr(line) => {
                            eprintln!("[backend] {}", String::from_utf8_lossy(&line));
                        }
                        CommandEvent::Error(err) => {
                            eprintln!("[backend] error: {err}");
                        }
                        CommandEvent::Terminated(payload) => {
                            eprintln!("[backend] proses berhenti: {payload:?}");
                        }
                        _ => {}
                    }
                }
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error saat membangun aplikasi Tauri")
        .run(|app_handle, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(child) = app_handle
                    .state::<BackendProcess>()
                    .0
                    .lock()
                    .expect("lock BackendProcess")
                    .take()
                {
                    let _ = child.kill();
                }
            }
        });
}
