import Cocoa
import UniformTypeIdentifiers
import AVFoundation

final class App: NSObject, NSApplicationDelegate, NSWindowDelegate {
    var root: URL {
        let relative = Bundle.main.object(forInfoDictionaryKey: "ProjectRootRelative") as? String ?? ".."
        return Bundle.main.bundleURL.deletingLastPathComponent().appendingPathComponent(relative).standardizedFileURL
    }
    var window: NSWindow!
    var source: URL?
    var job: URL?
    var worker: Process?
    var listeningWorker: Process?
    var player: AVAudioPlayer?
    var listeningPanel: NSPanel?
    var listeningStatus: NSTextField?
    var listeningSpinner: NSProgressIndicator?
    var listeningToken = UUID()
    var timer: Timer?
    var logHandle: FileHandle?
    var logURL: URL?
    var appIcon: NSImage?
    var language = UserDefaults.standard.string(forKey: "interfaceLanguage") ?? "de"
    var text: [String: String] = [:]
    var labels: [(NSTextField, String)] = []
    let fileLabel = NSTextField(labelWithString: "")
    let status = NSTextField(labelWithString: "")
    let counter = NSTextField(labelWithString: "0 / 0")
    let progress = NSProgressIndicator()
    let start = NSButton()
    let pause = NSButton()
    let result = NSButton()
    let choose = NSButton()
    let guide = NSButton()
    let voiceSamples = NSButton()
    let cardSamples = NSButton()
    let autoVoiceSample = NSButton(checkboxWithTitle: "", target: nil, action: nil)
    let logs = NSButton()
    let restore = NSButton()
    let modes = NSPopUpButton()
    let speech = NSPopUpButton()
    let languages = NSPopUpButton()
    let deck = NSPopUpButton()
    let field = NSPopUpButton()
    let backSpeech = NSPopUpButton()
    let voiceDE = NSPopUpButton()
    let voiceFR = NSPopUpButton()
    let voiceEN = NSPopUpButton()
    let voiceES = NSPopUpButton()
    let voiceRU = NSPopUpButton()
    let tagDE = NSTextField(string: "sound")
    let tagFR = NSTextField(string: "sound")
    let tagEN = NSTextField(string: "sound")
    let tagES = NSTextField(string: "sound")
    let tagRU = NSTextField(string: "sound")
    let russianVoiceCodes = ["Kseniya", "Xenia", "Baya", "Aidar", "Eugene"]
    let voiceCodes = ["F1", "F2", "F3", "F4", "F5", "M1", "M2", "M3", "M4", "M5"]
    let defaultVoices = ["de": "M5", "fr": "M1", "en": "M1", "es": "M1", "ru": "Kseniya"]
    var deckNames = [""]
    var fieldNames = ["*", "Front", "Back"]
    var inspecting = false
    var failure = false
    var mainWindowShown = false
    var tagRows = [NSStackView]()

    func t(_ key: String) -> String { text[key] ?? key }
    func read(_ url: URL) -> [String: Any]? {
        guard let data = try? Data(contentsOf: url) else { return nil }
        return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
    }
    func label(_ key: String) -> NSTextField {
        let view = NSTextField(labelWithString: "")
        labels.append((view, key))
        return view
    }
    func button(_ view: NSButton, _ action: Selector) {
        view.target = self; view.action = action; view.bezelStyle = .rounded
    }
    func row(_ views: [NSView]) -> NSStackView {
        let stack = NSStackView(views: views); stack.spacing = 12
        return stack
    }
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        let iconFile = Bundle.main.object(forInfoDictionaryKey: "CFBundleIconFile") as? String ?? "AppIcon.icns"
        if let path = Bundle.main.resourceURL?.appendingPathComponent(iconFile).path {
            appIcon = NSImage(contentsOfFile: path)
        }
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 760, height: 850), styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.delegate = self
        window.title = "Anki SOUND"
        let title = label("title"); title.font = .systemFont(ofSize: 28, weight: .bold)
        let subtitle = label("voices"); subtitle.textColor = .secondaryLabelColor
        let icon = NSImageView(); icon.image = appIcon; icon.imageScaling = .scaleProportionallyUpOrDown
        icon.translatesAutoresizingMaskIntoConstraints = false
        icon.widthAnchor.constraint(equalToConstant: 100).isActive = true
        icon.heightAnchor.constraint(equalToConstant: 100).isActive = true
        let heading = NSStackView(views: [title, subtitle]); heading.orientation = .vertical; heading.alignment = .leading; heading.spacing = 12
        let spacer = NSView()
        let header = row([heading, spacer, icon])
        languages.addItems(withTitles: ["Deutsch", "English", "Русский"])
        languages.target = self; languages.action = #selector(changeLanguage)
        button(choose, #selector(selectFile)); button(start, #selector(run)); button(pause, #selector(stop))
        button(result, #selector(reveal)); button(guide, #selector(showGuide)); button(logs, #selector(showLog)); button(voiceSamples, #selector(showVoiceSamples))
        button(cardSamples, #selector(listenToCards)); button(autoVoiceSample, #selector(toggleAutoVoiceSample))
        button(restore, #selector(loadLatest))
        modes.target = self; modes.action = #selector(selectionChanged)
        speech.target = self; speech.action = #selector(selectionChanged)
        start.keyEquivalent = "\r"
        deck.target = self; deck.action = #selector(selectionChanged)
        field.target = self; field.action = #selector(selectionChanged)
        backSpeech.target = self; backSpeech.action = #selector(selectionChanged)
        for selector in [voiceDE, voiceFR, voiceEN, voiceES] {
            selector.addItems(withTitles: voiceCodes)
            selector.target = self; selector.action = #selector(voiceChanged)
        }
        for field in [tagDE, tagFR, tagEN, tagES, tagRU] {
            field.target = self; field.action = #selector(selectionChanged)
            field.widthAnchor.constraint(equalToConstant: 150).isActive = true
        }
        voiceRU.addItems(withTitles: russianVoiceCodes)
        voiceRU.target = self; voiceRU.action = #selector(voiceChanged)
        autoVoiceSample.state = UserDefaults.standard.object(forKey: "autoVoiceSample") == nil || UserDefaults.standard.bool(forKey: "autoVoiceSample") ? .on : .off
        selectVoice(voiceDE, "M5"); selectVoice(voiceFR, "M1")
        selectVoice(voiceEN, "M1"); selectVoice(voiceES, "M1")
        counter.font = .monospacedDigitSystemFont(ofSize: 24, weight: .medium)
        progress.isIndeterminate = false; progress.minValue = 0; progress.maxValue = 1
        fileLabel.lineBreakMode = .byTruncatingMiddle
        let note = NSTextField(wrappingLabelWithString: ""); labels.append((note, "note")); note.textColor = .secondaryLabelColor
        let tagFirst = row([label("tagName"), NSTextField(labelWithString: "DE"), tagDE, NSTextField(labelWithString: "FR"), tagFR])
        let tagSecond = row([NSTextField(labelWithString: "EN"), tagEN, NSTextField(labelWithString: "ES"), tagES, NSTextField(labelWithString: "RU"), tagRU])
        tagRows = [tagFirst, tagSecond]
        let stack = NSStackView(views: [
            header, row([label("language"), languages, guide, voiceSamples]),
            row([choose, restore]), fileLabel,
            row([label("mode"), modes]),
            row([label("deck"), deck]),
            row([label("field"), field]),
            row([label("speech"), speech, label("backSpeech"), backSpeech]),
            tagFirst, tagSecond,
            row([label("voice"), NSTextField(labelWithString: "DE"), voiceDE, NSTextField(labelWithString: "FR"), voiceFR]),
            row([NSTextField(labelWithString: "EN"), voiceEN, NSTextField(labelWithString: "ES"), voiceES, NSTextField(labelWithString: "RU"), voiceRU]),
            row([cardSamples, autoVoiceSample]),
            counter, progress, status,
            row([start, pause, result, logs]), note
        ])
        stack.orientation = .vertical; stack.alignment = .leading; stack.spacing = 16
        stack.translatesAutoresizingMaskIntoConstraints = false
        window.contentView!.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: window.contentView!.leadingAnchor, constant: 28),
            stack.trailingAnchor.constraint(equalTo: window.contentView!.trailingAnchor, constant: -28),
            stack.topAnchor.constraint(equalTo: window.contentView!.topAnchor, constant: 24),
            header.widthAnchor.constraint(equalTo: stack.widthAnchor),
            deck.widthAnchor.constraint(equalToConstant: 380), field.widthAnchor.constraint(equalToConstant: 300),
            progress.widthAnchor.constraint(equalTo: stack.widthAnchor),
            fileLabel.widthAnchor.constraint(equalTo: stack.widthAnchor),
            note.widthAnchor.constraint(equalTo: stack.widthAnchor)
        ])
        localize()
        loadLatest()
        timer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { [weak self] _ in self?.refresh() }
        window.center(); window.makeKeyAndOrderFront(nil); mainWindowShown = true; NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        !hasActiveJob()
    }
    func localize() {
        if !["de", "en", "ru"].contains(language) { language = "de" }
        if let url = Bundle.main.url(forResource: language, withExtension: "json", subdirectory: "Interface"),
           let strings = read(url) as? [String: String] { text = strings }
        for (view, key) in labels { view.stringValue = t(key) }
        choose.title = t("choose"); start.title = t("start"); pause.title = t("pause")
        result.title = t("result"); guide.title = t("help"); logs.title = t("showLog"); restore.title = t("restore"); voiceSamples.title = t("voiceSamples")
        cardSamples.title = t("cardSamples"); autoVoiceSample.title = t("autoVoiceSample")
        let mode = max(0, modes.indexOfSelectedItem), voice = max(0, speech.indexOfSelectedItem)
        let backVoice = max(0, backSpeech.indexOfSelectedItem)
        let deckIndex = max(0, deck.indexOfSelectedItem), fieldIndex = max(0, field.indexOfSelectedItem)
        modes.removeAllItems(); modes.addItems(withTitles: [t("replace"), t("tagged"), t("deckMode")]); modes.selectItem(at: mode)
        speech.removeAllItems(); speech.addItems(withTitles: [t("de"), t("fr"), t("en"), t("es"), t("ru")]); speech.selectItem(at: voice)
        backSpeech.removeAllItems(); backSpeech.addItems(withTitles: [t("de"), t("fr"), t("en"), t("es"), t("ru")]); backSpeech.selectItem(at: backVoice)
        populateChoices(deckIndex: deckIndex, fieldIndex: fieldIndex)
        languages.selectItem(at: ["de", "en", "ru"].firstIndex(of: language) ?? 0)
        deck.setAccessibilityLabel(t("deck")); field.setAccessibilityLabel(t("field"))
        progress.setAccessibilityLabel(t("progress")); modes.setAccessibilityLabel(t("mode"))
        languages.setAccessibilityLabel(t("language")); speech.setAccessibilityLabel(t("speech"))
        backSpeech.setAccessibilityLabel(t("backSpeech"))
        let menu = NSMenu(); let item = NSMenuItem(); menu.addItem(item)
        let appMenu = NSMenu()
        let about = appMenu.addItem(withTitle: t("about"), action: #selector(showAbout), keyEquivalent: ""); about.target = self
        let help = appMenu.addItem(withTitle: t("help"), action: #selector(showGuide), keyEquivalent: "?"); help.target = self
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: t("close"), action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        appMenu.addItem(withTitle: t("quit"), action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.submenu = appMenu; NSApp.mainMenu = menu
        refresh()
    }
    @objc func changeLanguage() {
        language = ["de", "en", "ru"][languages.indexOfSelectedItem]
        UserDefaults.standard.set(language, forKey: "interfaceLanguage"); localize()
    }
    @objc func showAbout() {
        NSApp.orderFrontStandardAboutPanel(options: [
            .applicationName: "Anki SOUND",
            .applicationVersion: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "",
            .applicationIcon: appIcon ?? NSApp.applicationIconImage!,
            .credits: NSAttributedString(string: t("credits"))
        ])
    }
    @objc func showGuide() {
        NSWorkspace.shared.open(root.appendingPathComponent("docs/Guide-" + language + ".html"))
    }
    @objc func showVoiceSamples() {
        let output = root.appendingPathComponent("output")
        let pages = ((try? FileManager.default.contentsOfDirectory(at: output, includingPropertiesForKeys: [.contentModificationDateKey])) ?? [])
            .filter { $0.lastPathComponent.hasPrefix("voice-options-") }
            .sorted { ((try? $0.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast) > ((try? $1.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast) }
        guard let page = pages.first?.appendingPathComponent("index.html"), FileManager.default.fileExists(atPath: page.path) else {
            status.stringValue = t("samplesMissing"); return
        }
        let translated = page.deletingLastPathComponent().appendingPathComponent("index-" + language + ".html")
        NSWorkspace.shared.open(FileManager.default.fileExists(atPath: translated.path) ? translated : page)
    }
    @objc func toggleAutoVoiceSample() {
        UserDefaults.standard.set(autoVoiceSample.state == .on, forKey: "autoVoiceSample")
    }
    @objc func voiceChanged(_ sender: NSPopUpButton) {
        selectionChanged()
        guard autoVoiceSample.state == .on else { return }
        let selected: (String, String)?
        switch sender {
        case voiceDE: selected = (selectedVoice(voiceDE), "de")
        case voiceFR: selected = (selectedVoice(voiceFR), "fr")
        case voiceEN: selected = (selectedVoice(voiceEN), "en")
        case voiceES: selected = (selectedVoice(voiceES), "es")
        case voiceRU: selected = (voiceRU.titleOfSelectedItem ?? "Kseniya", "ru")
        default: selected = nil
        }
        guard let (voice, speechLanguage) = selected else { return }
        playVoiceSample(voice: voice, language: speechLanguage)
    }
    func latestVoiceSample(voice: String, language: String) -> URL? {
        let output = root.appendingPathComponent("output")
        let pages = ((try? FileManager.default.contentsOfDirectory(at: output, includingPropertiesForKeys: [.contentModificationDateKey])) ?? [])
            .filter { $0.lastPathComponent.hasPrefix("voice-options-") }
            .sorted { ((try? $0.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast) > ((try? $1.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast) }
        return pages.lazy.map { $0.appendingPathComponent(voice + "-" + language + ".wav") }.first { FileManager.default.fileExists(atPath: $0.path) }
    }
    func openListeningPanel(title: String, detail: String, loading: Bool) {
        stopListening(closePanel: true)
        let panel = NSPanel(contentRect: NSRect(x: 0, y: 0, width: 430, height: 170), styleMask: [.titled, .closable, .utilityWindow], backing: .buffered, defer: false)
        panel.title = title; panel.isFloatingPanel = true; panel.hidesOnDeactivate = false; panel.delegate = self
        let heading = NSTextField(labelWithString: title); heading.font = .systemFont(ofSize: 18, weight: .semibold)
        let detailLabel = NSTextField(wrappingLabelWithString: detail); detailLabel.textColor = .secondaryLabelColor
        let spinner = NSProgressIndicator(); spinner.style = .spinning; spinner.controlSize = .small
        if loading { spinner.startAnimation(nil) } else { spinner.isHidden = true }
        let close = NSButton(title: t("closeListening"), target: self, action: #selector(closeListening))
        let stack = NSStackView(views: [heading, detailLabel, spinner, close]); stack.orientation = .vertical; stack.alignment = .leading; stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false; panel.contentView?.addSubview(stack)
        NSLayoutConstraint.activate([stack.leadingAnchor.constraint(equalTo: panel.contentView!.leadingAnchor, constant: 24), stack.trailingAnchor.constraint(equalTo: panel.contentView!.trailingAnchor, constant: -24), stack.topAnchor.constraint(equalTo: panel.contentView!.topAnchor, constant: 22)])
        listeningPanel = panel; listeningStatus = detailLabel; listeningSpinner = spinner
        panel.center(); panel.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true)
    }
    @objc func closeListening() { stopListening(closePanel: true) }
    func stopListening(closePanel: Bool) {
        listeningToken = UUID()
        player?.stop(); player = nil
        if listeningWorker?.isRunning == true { listeningWorker?.terminate() }
        listeningWorker = nil
        guard closePanel, let panel = listeningPanel else { return }
        listeningPanel = nil; listeningStatus = nil; listeningSpinner = nil
        panel.delegate = nil; panel.close()
    }
    func play(_ audio: URL, detail: String) {
        do {
            player = try AVAudioPlayer(contentsOf: audio)
            listeningSpinner?.stopAnimation(nil); listeningSpinner?.isHidden = true
            listeningStatus?.stringValue = detail
            player?.play()
        } catch {
            listeningStatus?.stringValue = t("previewError")
        }
    }
    func playVoiceSample(voice: String, language: String) {
        guard let audio = latestVoiceSample(voice: voice, language: language) else { status.stringValue = t("samplesMissing"); return }
        openListeningPanel(title: t("voice") + " · " + voice, detail: t(language), loading: false)
        play(audio, detail: t(language))
    }
    @objc func listenToCards() {
        guard let source = source, worker?.isRunning != true, !inspecting else { return }
        openListeningPanel(title: t("cardSamples"), detail: t("previewPreparing"), loading: true)
        let token = listeningToken
        let process = Process(), output = Pipe(), errors = Pipe()
        process.executableURL = root.appendingPathComponent(".venv/bin/python")
        process.arguments = [root.appendingPathComponent("Sources/card_listen.py").path, source.path, "--selection", (try? String(data: JSONSerialization.data(withJSONObject: selection(), options: [.sortedKeys]), encoding: .utf8)) ?? "{}"]
        process.currentDirectoryURL = root; process.standardOutput = output; process.standardError = errors
        process.terminationHandler = { [weak self] completed in
            let data = output.fileHandleForReading.readDataToEndOfFile()
            DispatchQueue.main.async {
                guard let self = self, self.listeningToken == token, self.listeningPanel != nil else { return }
                self.listeningWorker = nil
                guard completed.terminationStatus == 0,
                      let result = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let path = result["audio"] as? String, let count = result["count"] as? Int else {
                    self.listeningSpinner?.stopAnimation(nil); self.listeningSpinner?.isHidden = true
                    self.listeningStatus?.stringValue = self.t("previewEmpty"); return
                }
                self.play(URL(fileURLWithPath: path), detail: self.t("previewPlaying") + " · " + String(count))
            }
        }
        do { try process.run(); listeningWorker = process }
        catch { listeningStatus?.stringValue = t("previewError") }
    }
    @objc func showLog() {
        if let log = logURL { NSWorkspace.shared.open(log) }
        else { NSWorkspace.shared.open(root.appendingPathComponent("output")) }
    }
    @objc func selectFile() {
        stopListening(closePanel: true)
        let panel = NSOpenPanel()
        panel.allowedContentTypes = ["apkg", "colpkg"].compactMap { UTType(filenameExtension: $0) }
        if panel.runModal() == .OK { source = panel.url; job = nil; failure = false; inspectSource(); refresh() }
    }
    @objc func selectionChanged() { stopListening(closePanel: true); job = nil; failure = false; refresh() }
    func selection() -> [String: String] {
        let mode = ["existing", "tag", "deck"][max(0, modes.indexOfSelectedItem)]
        let deckName = deckNames[max(0, deck.indexOfSelectedItem)]
        let fieldName = fieldNames[max(0, field.indexOfSelectedItem)]
        let voices = ["voice_de": selectedVoice(voiceDE), "voice_fr": selectedVoice(voiceFR),
                      "voice_en": selectedVoice(voiceEN), "voice_es": selectedVoice(voiceES), "voice_ru": voiceRU.titleOfSelectedItem ?? "Kseniya"]
        let defaults = ["voice_de": defaultVoices["de"]!, "voice_fr": defaultVoices["fr"]!,
                        "voice_en": defaultVoices["en"]!, "voice_es": defaultVoices["es"]!, "voice_ru": defaultVoices["ru"]!]
        if mode == "existing" {
            if deckName.isEmpty && fieldName == "*" && voices == defaults { return ["mode": mode] }
            var result = ["mode": mode, "deck": deckName, "field": fieldName]
            if voices != defaults { result.merge(voices) { _, newest in newest } }
            return result
        }
        var result = ["mode": mode, "deck": deckName, "field": fieldName, "language": ["de", "fr", "en", "es", "ru"][max(0, speech.indexOfSelectedItem)], "back_language": ["de", "fr", "en", "es", "ru"][max(0, backSpeech.indexOfSelectedItem)]]
        if mode == "tag" {
            result.merge(["tag_de": tagDE.stringValue, "tag_fr": tagFR.stringValue,
                          "tag_en": tagEN.stringValue, "tag_es": tagES.stringValue, "tag_ru": tagRU.stringValue]) { _, newest in newest }
        }
        result.merge(voices) { _, newest in newest }
        return result
    }
    func selectedVoice(_ selector: NSPopUpButton) -> String {
        voiceCodes[max(0, selector.indexOfSelectedItem)]
    }
    func selectVoice(_ selector: NSPopUpButton, _ code: String) {
        selector.selectItem(at: voiceCodes.firstIndex(of: code) ?? 0)
    }

    func populateChoices(deckIndex: Int, fieldIndex: Int) {
        deck.removeAllItems()
        deck.addItems(withTitles: deckNames.map { $0.isEmpty ? t("allDecks") : $0 })
        deck.selectItem(at: min(deckIndex, deckNames.count - 1))
        field.removeAllItems()
        field.addItems(withTitles: fieldNames.map { $0 == "*" ? t("bothFields") : $0 })
        field.selectItem(at: min(fieldIndex, fieldNames.count - 1))
    }
    func inspectSource() {
        guard let selected = source else { return }
        inspecting = true
        let script = root.appendingPathComponent("Sources/inspect_export.py")
        let interpreter = root.appendingPathComponent(".venv/bin/python")
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            let process = Process(), pipe = Pipe()
            process.executableURL = interpreter; process.arguments = [script.path, selected.path]
            process.standardOutput = pipe; process.standardError = FileHandle.nullDevice
            var data = Data()
            do { try process.run(); data = pipe.fileHandleForReading.readDataToEndOfFile(); process.waitUntilExit() }
            catch {}
            let values = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
            DispatchQueue.main.async {
                guard let self = self, self.source == selected else { return }
                self.inspecting = false
                let savedDeck = self.deckNames[max(0, self.deck.indexOfSelectedItem)]
                let savedField = self.fieldNames[max(0, self.field.indexOfSelectedItem)]
                if let decks = values?["decks"] as? [String], let fields = values?["fields"] as? [String] {
                    self.deckNames = [""] + decks
                    self.fieldNames = ["*"] + fields
                    self.populateChoices(deckIndex: self.deckNames.firstIndex(of: savedDeck) ?? 0, fieldIndex: self.fieldNames.firstIndex(of: savedField) ?? 0)
                } else { self.failure = true }
                self.refresh()
            }
        }
    }

    func jobs() -> [URL] {
        let urls = (try? FileManager.default.contentsOfDirectory(at: root.appendingPathComponent("output"), includingPropertiesForKeys: [.contentModificationDateKey])) ?? []
        return urls.filter { $0.lastPathComponent.hasPrefix("batch-") }.sorted {
            let a = (try? $0.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
            let b = (try? $1.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
            return a > b
        }
    }
    func hasActiveJob() -> Bool {
        if worker?.isRunning == true { return true }
        guard let job = job, let pid = read(job.appendingPathComponent("running.json"))?["pid"] as? Int else { return false }
        return kill(Int32(pid), 0) == 0
    }
    @objc func loadLatest() {
        for candidate in jobs() {
            if let state = read(candidate.appendingPathComponent("state.json")), let path = state["source"] as? String {
                job = candidate; source = URL(fileURLWithPath: path)
                let saved = state["selection"] as? [String: String] ?? ["mode": "existing"]
                modes.selectItem(at: ["existing", "tag", "deck"].firstIndex(of: saved["mode"] ?? "") ?? 0)
                let deckName = saved["deck"] ?? "", fieldName = saved["field"] ?? "*"
                deckNames = deckName.isEmpty ? [""] : ["", deckName]
                if !fieldNames.contains(fieldName) { fieldNames.append(fieldName) }
                populateChoices(deckIndex: deckNames.firstIndex(of: deckName) ?? 0, fieldIndex: fieldNames.firstIndex(of: fieldName) ?? 0)
                speech.selectItem(at: ["de", "fr", "en", "es", "ru"].firstIndex(of: saved["language"] ?? "de") ?? 0)
                backSpeech.selectItem(at: ["de", "fr", "en", "es", "ru"].firstIndex(of: saved["back_language"] ?? "de") ?? 0)
                selectVoice(voiceDE, saved["voice_de"] ?? defaultVoices["de"]!)
                selectVoice(voiceFR, saved["voice_fr"] ?? defaultVoices["fr"]!)
                selectVoice(voiceEN, saved["voice_en"] ?? defaultVoices["en"]!)
                selectVoice(voiceES, saved["voice_es"] ?? defaultVoices["es"]!)
                voiceRU.selectItem(withTitle: saved["voice_ru"] ?? defaultVoices["ru"]!)
                tagRU.stringValue = saved["tag_ru"] ?? "sound"
                tagDE.stringValue = saved["tag_de"] ?? "sound"; tagFR.stringValue = saved["tag_fr"] ?? "sound"
                tagEN.stringValue = saved["tag_en"] ?? "sound"; tagES.stringValue = saved["tag_es"] ?? "sound"
                inspectSource(); break
            }
        }
        refresh()
    }
    @objc func run() {
        stopListening(closePanel: true)
        guard let source = source, worker?.isRunning != true, !inspecting else { return }
        guard FileManager.default.isExecutableFile(atPath: root.appendingPathComponent(".venv/bin/python").path) else {
            status.stringValue = t("setup"); return
        }
        let savedJob = job
        if let job = savedJob { try? FileManager.default.removeItem(at: job.appendingPathComponent("pause.request")) }
        let output = root.appendingPathComponent("output")
        try? FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        let log = output.appendingPathComponent("run-" + UUID().uuidString + ".log")
        FileManager.default.createFile(atPath: log.path, contents: nil)
        guard let handle = try? FileHandle(forWritingTo: log) else { status.stringValue = t("logError"); return }
        logHandle = handle; logURL = log; failure = false
        let process = Process(); process.executableURL = URL(fileURLWithPath: "/usr/bin/caffeinate")
        var args = ["-i", root.appendingPathComponent(".venv/bin/python").path, "-u", root.appendingPathComponent("Sources/batch_export.py").path, source.path, "--detach"]
        if let job = savedJob { args += ["--resume-job", job.path] }
        for (key, value) in selection().sorted(by: {$0.key < $1.key}) { args += ["--" + key.replacingOccurrences(of: "_", with: "-"), value] }
        process.arguments = args; process.currentDirectoryURL = root
        process.standardOutput = handle; process.standardError = handle
        process.terminationHandler = { [weak self] process in
            DispatchQueue.main.async {
                self?.logHandle?.closeFile(); self?.logHandle = nil
                self?.failure = process.terminationStatus != 0 && process.terminationStatus != 130
                self?.refresh()
            }
        }
        do { try process.run(); worker = process; status.stringValue = t("preparing"); start.isEnabled = false }
        catch { handle.closeFile(); logHandle = nil; failure = true; status.stringValue = t("error") }
    }
    @objc func stop() {
        guard let job = job else { return }
        do { try Data().write(to: job.appendingPathComponent("pause.request")); status.stringValue = t("pausing") }
        catch { status.stringValue = t("error") }
    }
    @objc func reveal() {
        guard let job = job, let value = read(job.appendingPathComponent("result.json")), let path = value["path"] as? String else { return }
        NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: path)])
    }
    func refresh() {
        fileLabel.stringValue = source?.lastPathComponent ?? t("noFile")
        if job == nil, let source = source {
            job = jobs().first {
                guard let state = read($0.appendingPathComponent("state.json")) else { return false }
                return state["source"] as? String == source.path && (state["selection"] as? [String: String] ?? ["mode": "existing"]) == selection()
            }
        }
        var active = worker?.isRunning == true
        if let job = job, let state = read(job.appendingPathComponent("state.json")) {
            let done = (state["completed"] as? [String])?.count ?? 0
            let total = (state["records"] as? [Any])?.count ?? 0
            let skipped = (state["rejected"] as? [Any])?.count ?? 0
            let formatter = NumberFormatter(); formatter.numberStyle = .decimal
            formatter.locale = Locale(identifier: language)
            counter.stringValue = "\(formatter.string(from: NSNumber(value: done)) ?? "") / \(formatter.string(from: NSNumber(value: total)) ?? "")"
            progress.doubleValue = total > 0 ? Double(done) / Double(total) : 0
            if let pid = read(job.appendingPathComponent("running.json"))?["pid"] as? Int { active = active || kill(Int32(pid), 0) == 0 }
            let ready = read(job.appendingPathComponent("result.json"))?["verified"] as? Bool == true
            result.isEnabled = ready
            status.stringValue = t(ready ? "ready" : (active ? (done == total ? "packaging" : "running") : "resume"))
            if skipped > 0 { status.stringValue += " · " + t("skipped") + ": \(skipped)" }
            start.isEnabled = !active && !ready
        } else {
            counter.stringValue = "0 / 0"; progress.doubleValue = 0
            start.isEnabled = source != nil && !active; result.isEnabled = false
            status.stringValue = t(active ? "preparing" : "idle")
        }
        if failure { status.stringValue = t("error") }
        pause.isEnabled = active && job != nil
        cardSamples.isEnabled = source != nil && !active && !inspecting && listeningWorker?.isRunning != true
        autoVoiceSample.isEnabled = !active
        choose.isEnabled = !active; restore.isEnabled = !active; modes.isEnabled = !active
        deck.isEnabled = !active && !inspecting
        field.isEnabled = !active && !inspecting
        speech.isEnabled = !active && modes.indexOfSelectedItem == 2
        backSpeech.isEnabled = speech.isEnabled && fieldNames[max(0, field.indexOfSelectedItem)] == "*"
        for selector in [voiceDE, voiceFR, voiceEN, voiceES] { selector.isEnabled = !active }
        voiceRU.isEnabled = !active
        voiceRU.setAccessibilityLabel(t("ru") + " · " + t("voice"))
        tagRU.setAccessibilityLabel(t("ru") + " · " + t("tagName"))
        let isTagMode = modes.indexOfSelectedItem == 1
        for row in tagRows { row.isHidden = !isTagMode }
        for field in [tagDE, tagFR, tagEN, tagES, tagRU] { field.isEnabled = !active && isTagMode }
        if inspecting { start.isEnabled = false; status.stringValue = t("reading") }
        if modes.indexOfSelectedItem == 2 && deck.indexOfSelectedItem == 0 { start.isEnabled = false; status.stringValue = t("selectDeck") }
        if mainWindowShown && !window.isVisible && !active { NSApp.terminate(nil) }
    }
    func windowWillClose(_ notification: Notification) {
        guard let closed = notification.object as? NSWindow else { return }
        if closed === listeningPanel {
            listeningToken = UUID()
            player?.stop(); player = nil
            if listeningWorker?.isRunning == true { listeningWorker?.terminate() }
            listeningWorker = nil; listeningPanel = nil; listeningStatus = nil; listeningSpinner = nil
        } else if closed === window {
            stopListening(closePanel: true)
        }
    }
}
let app = NSApplication.shared
let delegate = App()
app.delegate = delegate
app.run()
