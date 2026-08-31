;;; records.el --- Chat panel for the blyant records site  -*- lexical-binding: t; -*-

;; Author: tb4
;; Version: 0.1.0
;; Package-Requires: ((emacs "27.1"))
;; Homepage: https://codeberg.org/blyant/records
;; SPDX-License-Identifier: MIT

;;; Commentary:

;; The Emacs front end for blyant records — a publish-your-conversations site
;; where every record is a Markdown file in your own repo.
;;
;; The package holds no logic of its own.  Every action runs the `records' CLI
;; (recordkit, `pipx install recordkit'), which does the frontmatter, the
;; naming, the git work and the publishing.  If Emacs needs something the CLI
;; cannot do, the CLI grows, not this package.
;;
;; Mechanical only: no model is involved, and none is needed.
;;
;;   M-x records            open the chat panel
;;   /all #linux How To     start a recording
;;   hello                  appended to it verbatim
;;   /esc                   stop

;;; Code:

(require 'json)
(require 'subr-x)

(defgroup records nil
  "Write records for a blyant records site."
  :group 'external
  :prefix "records-")

(defcustom records-bin "records"
  "The recordkit CLI to run.
An absolute path if `records' is not on `exec-path'."
  :type 'string
  :group 'records)

(defcustom records-ollama-endpoint nil
  "Reserved.  Two-sided \\=`/record\\=' in Emacs is not wired yet.
Setting this changes nothing today; every command is mechanical."
  :type '(choice (const :tag "None" nil) string)
  :group 'records)

(defconst records-commands
  '(("record" . "Start recording (user-only in Emacs today)")
    ("all"    . "Start a user-only recording")
    ("me"     . "Start a draft recording, kept off the site")
    ("esc"    . "Stop recording")
    ("stick"  . "Feature a record")
    ("gc"     . "Commit")
    ("gcp"    . "Commit and push")
    ("cpd"    . "Commit, push, deploy")
    ("myname" . "Save your name locally")
    ("mucke"  . "Stamp the now-playing track")
    ("airtime" . "Human vs Assistant token share")
    ("config" . "Show the resolved records directory"))
  "The shared slash registry — the same commands the other plugins offer.")

(defvar records--recording nil
  "Path of the record currently being written, or nil.")

(defconst records--buffer-name "*records*")

;;; The CLI

(defun records--run (command &rest args)
  "Run COMMAND with ARGS through the CLI and return the parsed JSON alist.
Signal an error when the CLI is missing, mute, or reports one."
  (let* ((argv (append (list command) (delq nil args)))
         (parsed
          (with-temp-buffer
            (unless (or (file-name-absolute-p records-bin)
                        (executable-find records-bin))
              (error "No `%s' on PATH — install it with `pipx install recordkit'"
                     records-bin))
            (apply #'call-process records-bin nil t nil argv)
            (let ((out (buffer-string)))
              (when (string-empty-p (string-trim out))
                (error "No response from `%s %s'" records-bin command))
              (condition-case err
                  (let ((json-object-type 'alist)
                        (json-array-type 'list))
                    (json-read-from-string out))
                (error (error "Invalid CLI response: %s (%s)"
                              (string-trim out) (error-message-string err))))))))
    (let ((failure (alist-get 'error parsed)))
      (when failure (error "%s" failure)))
    parsed))

;;; The panel

(defun records--say (text &optional face)
  "Append TEXT to the records buffer, propertized with FACE."
  (with-current-buffer (get-buffer-create records--buffer-name)
    (let ((inhibit-read-only t))
      (save-excursion
        (goto-char (point-max))
        (insert (if face (propertize text 'face face) text) "\n")))
    (dolist (window (get-buffer-window-list nil nil t))
      (set-window-point window (point-max)))))

(defun records--slash (cmd args)
  "Dispatch slash command CMD with its raw ARGS string."
  (cond
   ((member cmd '("record" "all" "me"))
    (let* ((draft (string= cmd "me"))
           (result (records--run "new" args (and draft "--draft"))))
      (setq records--recording (alist-get 'path result))
      (records--say (format "Recording (%s): %s" cmd records--recording) 'success)))

   ((string= cmd "esc")
    (setq records--recording nil)
    (records--say "Recording stopped." 'success))

   ((string= cmd "stick")
    (when (string-empty-p args) (error "A slug is required: /stick <slug>"))
    (records--say (format "Featured: %s"
                          (alist-get 'path (records--run "stick" "--slug" args)))
                  'success))

   ((member cmd '("gc" "gcp" "cpd"))
    (let ((message (if (string-empty-p args) (read-string "Commit message: ") args))
          (push (not (string= cmd "gc"))))
      (when (string-empty-p message) (error "Commit message required"))
      (records--run "commit" "--message" message
                    (and push "--push") (and (string= cmd "cpd") "--deploy"))
      (records--say (format "Commit %s: %s" (if push "(pushed)" "(staged)") message)
                    'success)))

   ((string= cmd "myname")
    (let ((name (if (string-empty-p args) (read-string "Your name: ") args)))
      (unless (string-empty-p name)
        (records--run "myname" name)
        (records--say (format "Saved your name: %s" name) 'success))))

   ((string= cmd "mucke")
    (unless records--recording
      (error "/mucke stamps the track into the record being written — start one first"))
    (let ((result (records--run "mucke" "--file" records--recording)))
      (records--say (format "Mucke: %s • %s"
                            (alist-get 'title result) (alist-get 'artist result))
                    'success)))

   ((string= cmd "airtime")
    (unless records--recording
      (error "/airtime measures the record being written — start one first"))
    (records--say (alist-get 'line (records--run "airtime" "--file" records--recording))
                  'success))

   ((string= cmd "config")
    (records--say (format "Records dir: %s"
                          (alist-get 'records_dir (records--run "config")))
                  'success))

   (t (error "Unknown command: /%s" cmd))))

;;;###autoload
(defun records-send (line)
  "Handle LINE exactly as if it had been typed into the panel."
  (interactive (list (read-string "records> ")))
  (setq line (string-trim line))
  (unless (string-empty-p line)
    (records--say (concat "> " line) 'shadow)
    (condition-case err
        (if (string-prefix-p "/" line)
            (let* ((body (substring line 1))
                   (split (string-match-p "[ \t]" body))
                   (cmd (if split (substring body 0 split) body))
                   (args (if split (string-trim (substring body split)) "")))
              (records--slash cmd args))
          (if records--recording
              (records--run "append" "--file" records--recording "--text" line)
            (records--say "Nothing is being recorded — /record, /all or /me starts one."
                          'shadow)))
      (error (records--say (concat "ERROR: " (error-message-string err)) 'error)))))

(defun records-prompt ()
  "Read one line and send it."
  (interactive)
  (records-send
   (completing-read "records> "
                    (mapcar (lambda (c) (concat "/" (car c))) records-commands)
                    nil nil)))

(defvar records-mode-map
  (let ((map (make-sparse-keymap)))
    (define-key map (kbd "RET") #'records-prompt)
    (define-key map (kbd "i") #'records-prompt)
    (define-key map (kbd "q") #'quit-window)
    map)
  "Keymap for `records-mode'.")

(define-derived-mode records-mode special-mode "Records"
  "Major mode for the records chat panel."
  (setq-local truncate-lines nil))

;;;###autoload
(defun records ()
  "Open the records chat panel in a window at the bottom."
  (interactive)
  (let ((buffer (get-buffer-create records--buffer-name)))
    (with-current-buffer buffer
      (unless (derived-mode-p 'records-mode)
        (records-mode)
        (let ((inhibit-read-only t))
          (insert "Records chat — RET to type a /command or a message. q to close.\n\n"))))
    (pop-to-buffer buffer '((display-buffer-at-bottom)
                            (window-height . 0.4)))))

(provide 'records)

;;; records.el ends here
