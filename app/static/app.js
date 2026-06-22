const SUPPORTED_LANGUAGES = ["de", "en"];

function detectBrowserLanguage() {
  const languages = Array.isArray(navigator.languages) && navigator.languages.length
    ? navigator.languages
    : [navigator.language || navigator.userLanguage || ""];
  for (const candidate of languages) {
    const prefix = String(candidate || "").trim().toLowerCase().split("-")[0];
    if (SUPPORTED_LANGUAGES.includes(prefix)) return prefix;
  }
  return "en";
}

const savedLanguage = localStorage.getItem("marketplacelens.language");

const state = {
  profiles: [],
  selectedProfile: null,
  listingView: localStorage.getItem("marketplacelens.listingView") || "list",
  language: savedLanguage || detectBrowserLanguage(),
  theme: localStorage.getItem("marketplacelens.theme") || "light",
  listingPage: 0,
  watchlistPage: 0,
  pageSize: Number(localStorage.getItem("marketplacelens.pageSize") || 100),
  reviewQueue: [],
  reviewIndex: 0,
  reviewPointer: null,
  watchlists: [],
  defaultWatchlistId: null,
  aiEnabled: false,
  aiAssessmentsEnabled: false,
  aiAssessmentsAutoEnabled: false,
  aiAssessmentsNewEnabled: false,
  autoAssessmentBatches: new Set(),
  autoAssessmentRunning: false,
  wizardStep: 0,
  currentUser: null,
  accountProfile: null,
  users: [],
  version: null,
  locationMap: null,
  locationMarker: null,
  locationCircle: null,
  locationResolveToken: 0,
  appOpenCheckStarted: false,
  settingsTab: "notifications",
  currentView: "dashboard",
};

const AUTO_ASSESSMENT_BATCH_LIMIT = 8;

const translations = {
  en: {
    "brand.subtitle": "self-hosted listing watcher",
    "nav.dashboard": "Dashboard",
    "nav.profiles": "Jobs",
    "nav.listings": "Listings",
    "nav.review": "Swipe",
    "nav.watchlist": "Watchlist",
    "nav.settings": "Settings",
    "top.eyebrow": "Local marketplace watcher",
    "action.refresh": "Refresh",
    "action.logout": "Logout",
    "action.delete": "Delete",
    "theme.light": "Light",
    "theme.dark": "Dark",
    "theme.switchToLight": "Light",
    "theme.switchToDark": "Dark",
    "summary.activeProfiles": "Active profiles",
    "summary.newListings": "New listings",
    "summary.watchlist": "Watchlist",
    "summary.hidden": "Hidden",
    "summary.notified": "Notified",
    "summary.runErrors": "Run errors",
    "dashboard.recentRuns": "Recent runs",
    "dashboard.recentRunsSubtitle": "Last source checks and connector status.",
    "dashboard.clearErrors": "Clear run errors",
    "dashboard.deleteError": "Delete error",
    "dashboard.sources": "Sources",
    "dashboard.sourcesSubtitle": "Jobs and collected listings by marketplace.",
    "profiles.title": "Jobs",
    "profiles.subtitle": "Saved marketplace jobs grouped by source.",
    "profiles.editorSubtitle": "Create a job from a provider URL, then add filters and notifications.",
    "profiles.guidedSetup": "Quick job",
    "profiles.quickJob": "Quick job",
    "profiles.manual": "New job",
    "profiles.newJob": "New job",
    "profiles.all": "All profiles",
    "profile.new": "New job",
    "profile.edit": "Edit job",
    "profile.searchTitle": "Job",
    "profile.searchSubtitle": "Name this watch so it is easy to scan later",
    "profile.name": "Job name",
    "profile.source": "Source",
    "profile.sourceTitle": "Provider",
    "profile.sourceSubtitle": "Pick the marketplace and paste the sorted search URL.",
    "profile.searchUrl": "Search URL",
    "profile.urlParameters": "URL parameters",
    "profile.urlQuery": "Search",
    "profile.urlCategory": "Category",
    "profile.urlLocation": "Location",
    "urlParams.key": "Parameter",
    "urlParams.value": "Value",
    "urlParams.apply": "Apply",
    "urlParams.add": "Add parameter",
    "urlParams.remove": "Remove parameter",
    "profile.openSource": "Open source",
    "profile.filtersTitle": "Criteria",
    "profile.filtersSubtitle": "Local filters applied after the search page is fetched",
    "profile.locationHint": "Location hint",
    "profile.minPrice": "Min price",
    "profile.maxPrice": "Max price",
    "profile.minPriceShort": "Min",
    "profile.maxPriceShort": "Max",
    "profile.maxAge": "Oldest listing",
    "profile.maxAgeShort": "Max age",
    "profile.maxAgeDays": "{days} days",
    "profile.pollInterval": "Poll interval",
    "profile.keywordTitle": "Keyword rules",
    "profile.keywordSubtitle": "Match, require, or hide terms from listings",
    "profile.include": "Include",
    "profile.required": "Required",
    "profile.exclude": "Exclude",
    "profile.hiddenCategories": "Hidden categories",
    "keyword.add": "Add keyword",
    "keyword.remove": "Remove {item}",
    "filter.ruleType": "Rule",
    "filter.typeRequired": "Only show when text contains",
    "filter.typeExclude": "Hide when text contains",
    "filter.typeInclude": "Prefer when text contains",
    "filter.term": "Word or phrase",
    "filter.termPlaceholder": "washing",
    "filter.add": "Add rule",
    "filter.empty": "No keyword rules yet",
    "filter.requiredRule": "Only show listings when title or description contains \"{term}\"",
    "filter.excludeRule": "Hide listings when title or description contains \"{term}\"",
    "filter.includeRule": "Prefer listings when title or description contains \"{term}\"",
    "profile.automationTitle": "Automation & notifications",
    "profile.automationSubtitle": "Choose whether this job runs in the background and sends notifications.",
    "profile.enabled": "enabled",
    "profile.paused": "paused",
    "profile.everyMinutes": "every {minutes} min",
    "profile.save": "Save job",
    "profile.runNow": "Run now",
    "wizard.title": "Quick job",
    "wizard.subtitle": "I will guide you through source, search, filters, and automation.",
    "wizard.aiPrompt": "Describe the search in one sentence",
    "wizard.aiCreate": "Create with AI",
    "wizard.stepSource": "Source",
    "wizard.stepSearch": "Search",
    "wizard.stepFilters": "Filters",
    "wizard.stepReview": "Review",
    "wizard.sourcePrompt": "Where should I search?",
    "wizard.sourceHelp": "Choose the marketplace and optionally narrow it to a category.",
    "wizard.searchPrompt": "What should the job find?",
    "wizard.searchHelp": "Name the item as you would search for it, then add optional price and location limits.",
    "wizard.filterPrompt": "What should I prefer or ignore?",
    "wizard.filterHelp": "Add words that must appear or words that should hide a listing.",
    "wizard.reviewPrompt": "How should the job run?",
    "wizard.reviewHelp": "Decide whether this job should run automatically and send notifications.",
    "wizard.summaryTitle": "Job preview",
    "wizard.summaryEmpty": "Add a search term and I will assemble the job.",
    "wizard.back": "Back",
    "wizard.next": "Next",
    "wizard.query": "What should be found?",
    "wizard.source": "Source",
    "wizard.category": "Category",
    "wizard.allCategories": "All categories",
    "wizard.maxPrice": "Maximum price",
    "wizard.maxAge": "Oldest listing",
    "wizard.location": "Location",
    "location.textMode": "ZIP / place",
    "location.mapMode": "Map",
    "location.query": "ZIP code or place",
    "location.radius": "Radius",
    "location.wholePlace": "Whole place",
    "location.coordinates": "Coordinates",
    "location.resolvedPlace": "Resolved place",
    "location.resolving": "Resolving place...",
    "location.mapHint": "Click on the map to set an approximate center point",
    "location.help": "Use a ZIP/place like Kleinanzeigen, or click a map point and choose a radius.",
    "location.mapPrefix": "Map point",
    "wizard.mustInclude": "Must include",
    "wizard.hideWords": "Hide words",
    "wizard.create": "Create job",
    "wizard.manualForm": "Use manual form",
    "listingTypes.title": "Listing types",
    "listingTypes.offers": "Offers",
    "listingTypes.wanted": "Wanted",
    "listingTypes.help": "Both selected means all listing types.",
    "listingTypes.all": "All listing types",
    "listingTypes.offersOnly": "Offers only",
    "listingTypes.wantedOnly": "Wanted only",
    "form.backgroundPolling": "Background polling",
    "form.telegram": "Telegram",
    "form.webhook": "Webhook",
    "form.telegramNotifications": "Telegram notifications",
    "form.webhookNotifications": "Webhook notifications",
    "notifications.pollingHint": "Run this job automatically.",
    "notifications.telegramHint": "Send new matches to Telegram.",
    "notifications.webhookHint": "Post new matches to your webhook.",
    "source.kleinanzeigenHelp": "Paste a public Kleinanzeigen search URL.",
    "source.facebookHelp": "Use a Marketplace search/category URL. The Facebook settings guide helps with browser sessions.",
    "source.mobiledeHelp": "Paste a public mobile.de search result URL.",
    "source.marktplaatsHelp": "Paste a public Marktplaats.nl search result URL.",
    "source.generic": "Generic HTML",
    "source.genericHelp": "Use a simple listing result page.",
    "jobSummary.nameMissing": "Name missing",
    "jobSummary.urlMissing": "URL missing",
    "jobSummary.provider": "Provider",
    "jobSummary.interval": "{minutes} min",
    "jobSummary.pollingOn": "Polling on",
    "jobSummary.pollingOff": "Polling off",
    "jobSummary.telegramOn": "Telegram on",
    "jobSummary.telegramOff": "Telegram off",
    "jobSummary.webhookOn": "Webhook on",
    "jobSummary.webhookOff": "Webhook off",
    "listings.title": "Browse listings",
    "listings.subtitle": "Scroll, filter, switch between list and tiles, or open the original listing.",
    "listings.settings": "Filters and display",
    "listings.searchPlaceholder": "Search title, location, category",
    "listings.allStatuses": "All statuses",
    "listings.includeHidden": "Show hidden/seen",
    "listings.runSelectedJob": "Run job",
    "listings.runSelectedJobHint": "Select a job to run it from here.",
    "listings.resultSummary": "{total} matches with current filters",
    "watchlist.title": "Watchlist",
    "watchlist.subtitle": "Saved listings you want to compare or revisit later.",
    "review.title": "Swipe",
    "review.subtitle": "Scan one listing at a time with image, price, location, and source data.",
    "review.empty": "No listings to review",
    "review.emptyHint": "Run a job or reset seen listings to fill this queue.",
    "review.watch": "Watchlist",
    "review.seen": "Seen, next",
    "review.open": "Open original",
    "review.doubleClick": "Double-click to add to watchlist",
    "review.swipe": "Swipe to mark seen",
    "review.reason": "Match score {score}",
    "status.new": "New",
    "status.notified": "Notified",
    "status.hidden": "Hidden",
    "status.seen": "Seen",
    "sort.dateDesc": "Newest first",
    "sort.priceAsc": "Price low-high",
    "sort.priceDesc": "Price high-low",
    "sort.scoreDesc": "Best score",
    "view.list": "List",
    "view.scan": "Scan",
    "view.tiles": "Tiles",
    "pagination.pageSize": "Per page",
    "pagination.prev": "Prev",
    "pagination.next": "Next",
    "pagination.range": "{start}-{end} / {total}",
    "settings.notifications": "Notifications",
    "settings.notificationsSubtitle": "Configure delivery channels for job matches and tests.",
    "settings.adminCategory": "Admin settings",
    "settings.accountCategory": "Account",
    "settings.telegram": "Telegram",
    "settings.telegramHint": "Bot messages to the configured chat.",
    "settings.webhook": "Webhook",
    "settings.webhookHint": "HTTP delivery to your configured receiver.",
    "settings.deliveryRules": "Delivery rules",
    "settings.deliveryRulesHint": "Job cards choose whether Telegram and webhook receive new matches.",
    "settings.perJob": "per job",
    "settings.facebookShort": "Facebook",
    "settings.aiShort": "AI",
    "settings.usersShort": "Users",
    "settings.botToken": "Bot token",
    "settings.chatId": "Chat ID",
    "settings.webhookUrl": "Webhook URL",
    "settings.rateLimit": "Global rate limit seconds",
    "settings.watchlists": "Watchlists",
    "settings.watchlistsSubtitle": "Choose the default list used by the normal Watch click.",
    "settings.defaultWatchlist": "Default watchlist",
    "settings.newWatchlist": "New watchlist",
    "settings.createWatchlist": "Create list",
    "settings.ai": "AI features",
    "settings.aiSubtitle": "Generate buyer messages and quick-job search drafts when a provider is configured.",
    "settings.aiEnabled": "Enable AI features",
    "settings.aiAssessmentsEnabled": "Show AI listing assessments",
    "settings.aiAssessmentsAutoEnabled": "Automatically assess visible listings",
    "settings.aiAssessmentsNewEnabled": "Assess new listings during job runs",
    "settings.aiAssessmentCostWarning": "AI assessments send listing title, price, description, and match data to the configured provider. New-listing and visible-listing automation can use many tokens.",
    "settings.aiTest": "Test AI",
    "settings.aiProvider": "Provider",
    "settings.aiApiKey": "API key",
    "settings.aiBaseUrl": "Base URL",
    "settings.aiModel": "Model",
    "settings.aiTone": "Tone",
    "settings.aiTonePolite": "Very polite",
    "settings.aiToneNormal": "Normal",
    "settings.aiToneCheeky": "Cheeky",
    "settings.facebook": "Facebook Marketplace session",
    "settings.facebookSubtitle": "Use a Marketplace URL first. Add your own browser Cookie only if Facebook blocks the server request.",
    "settings.facebookGuideTitle": "Setup guide",
    "settings.facebookGuideStep1": "Open Facebook Marketplace in your browser and set the search, category, location, and filters exactly as you want them.",
    "settings.facebookGuideStep2": "Copy the browser address and paste it into a new Facebook job. Try Run now once before adding cookies.",
    "settings.facebookGuideStep3": "Only if the run says Facebook needs a logged-in session: open browser developer tools, copy the Cookie value or Cookie: request header from your own Marketplace request, and paste it below. It must include c_user and xs.",
    "settings.facebookGuideStep4": "Cookies stay local, can expire, and can be replaced by pasting a fresh one. MarketPlaceLens stores no Facebook password and does not bypass login/CAPTCHA protections.",
    "settings.facebookOpen": "Open Marketplace",
    "settings.facebookCookie": "Cookie header",
    "settings.facebookCookieHint": "Use only your own account/session. Paste a Cookie that includes c_user and xs, a Cookie: line, or a full browser request header block. Leave ******** unchanged to keep the saved cookie.",
    "settings.save": "Save settings",
    "settings.sendTest": "Send test",
    "settings.sendWebhookTest": "Send webhook test",
    "settings.password": "Password",
    "settings.passwordSubtitle": "Change your local password for this app.",
    "settings.profile": "Personal details",
    "settings.profileSubtitle": "Used when AI inquiry texts are generated for your listings.",
    "settings.displayName": "Name",
    "settings.buyerLocation": "Your location",
    "settings.contactHint": "Contact note",
    "settings.inquirySignature": "Message signature",
    "settings.saveProfile": "Save details",
    "settings.currentPassword": "Current password",
    "settings.newPassword": "New password",
    "settings.repeatPassword": "Repeat new password",
    "settings.changePassword": "Change password",
    "settings.users": "Users & roles",
    "settings.usersSubtitle": "Admins can create accounts and decide who may change global settings.",
    "settings.newUser": "New user",
    "settings.username": "Username",
    "settings.role": "Role",
    "settings.roleAdmin": "Admin",
    "settings.roleUser": "User",
    "settings.enabled": "Enabled",
    "settings.disabled": "Disabled",
    "settings.userPassword": "Initial password",
    "settings.createUser": "Create user",
    "settings.saveUser": "Save user",
    "settings.deleteUser": "Delete user",
    "settings.editUser": "Edit user",
    "empty.noRuns": "No runs yet",
    "empty.noRunsHint": "Create a profile and run it manually.",
    "empty.noProfiles": "No profiles",
    "empty.noProfilesHint": "Add the first search URL on the right.",
    "empty.sourceProfiles": "No {source} jobs yet",
    "empty.noListings": "No listings",
    "empty.noListingsHint": "Adjust filters or run a profile.",
    "empty.noWatchlist": "No watchlisted listings",
    "empty.noWatchlistHint": "Use the star button on a listing to save it here.",
    "listing.noImage": "No image available",
    "listing.noPrice": "no price",
    "listing.noLocation": "no location",
    "listing.map": "Map",
    "listing.locationMapTitle": "Listing location",
    "listing.locationMapOpen": "Open in OpenStreetMap",
    "listing.locationMapLoading": "Loading map...",
    "listing.locationMapUnavailable": "No map position found for this location.",
    "listing.postedAt": "Listed",
    "listing.unknownPostedAt": "unknown",
    "listing.postcode": "ZIP",
    "listing.place": "Place",
    "listing.score": "score {score}",
    "listing.addWatchlist": "Watch",
    "listing.removeWatchlist": "Remove",
    "listing.watchMenu": "Choose watchlist",
    "listing.newWatchlistPrompt": "New watchlist name",
    "listing.addToWatchlist": "Add to {name}",
    "listing.aiInquiry": "AI text",
    "listing.aiAssessment": "AI assessment",
    "listing.aiAssessmentEmpty": "No AI assessment yet.",
    "listing.contacted": "Contacted",
    "listing.notContacted": "Not contacted",
    "listing.markContacted": "Contacted",
    "listing.unmarkContacted": "Undo contacted",
    "availability.active": "Active",
    "availability.reserved": "Reserved",
    "availability.deleted": "Deleted",
    "availability.unknown": "Not checked",
    "listing.seen": "Seen",
    "listing.hide": "Hide",
    "listing.new": "New",
    "date.never": "never",
    "toast.listingHidden": "Listing hidden",
    "toast.listingSeen": "Listing marked as seen",
    "toast.listingNew": "Listing moved back to new",
    "toast.contactedChanged": "Contact flag updated",
    "toast.watchlistAdded": "Added to watchlist",
    "toast.watchlistAddedTo": "Added to {name}",
    "toast.watchlistCreated": "Watchlist created",
    "toast.watchlistRemoved": "Removed from watchlist",
    "toast.inquiryGenerated": "Inquiry text generated",
    "toast.assessmentGenerated": "AI assessment saved",
    "toast.searchDraftCreated": "Search draft created",
    "toast.aiTestOk": "AI provider answered",
    "toast.inquiryCopied": "Inquiry copied",
    "inquiry.title": "AI inquiry text",
    "inquiry.copy": "Copy",
    "inquiry.close": "Close",
    "toast.passwordMismatch": "New passwords do not match",
    "toast.passwordChanged": "Password changed",
    "toast.userSaved": "User saved",
    "toast.userDeleted": "User deleted",
    "toast.profileSaved": "Profile saved",
    "toast.saveProfileFirst": "Save a profile first",
    "toast.selectJobFirst": "Select a job first",
    "toast.runStarted": "Run started",
    "toast.runComplete": "Run complete: {new} new, {hidden} hidden, {duplicates} duplicate",
    "toast.runErrorDeleted": "Run error deleted",
    "toast.runErrorsCleared": "{deleted} run errors cleared",
    "toast.profileDeleted": "Profile deleted",
    "toast.searchRequired": "Search term is required",
    "toast.facebookUrlRequired": "Facebook Marketplace needs a reachable Marketplace URL.",
    "toast.facebookSearchQueryRequired": "Facebook Marketplace search URLs need a search term.",
    "toast.listingTypeRequired": "Select at least one Kleinanzeigen listing type",
    "toast.settingsSaved": "Settings saved",
    "toast.profileSaved": "Personal details saved",
    "toast.telegramSent": "Telegram test sent",
    "toast.webhookSent": "Webhook test sent",
    "toast.openCheckStarted": "Checking active jobs now",
  },
  de: {
    "brand.subtitle": "selbst gehosteter Anzeigen-Watcher",
    "nav.dashboard": "Dashboard",
    "nav.profiles": "Jobs",
    "nav.listings": "Listings",
    "nav.review": "Swipen",
    "nav.watchlist": "Watchlist",
    "nav.settings": "Einstellungen",
    "top.eyebrow": "Lokaler Marketplace-Watcher",
    "action.refresh": "Aktualisieren",
    "action.logout": "Abmelden",
    "action.delete": "Löschen",
    "theme.light": "Hell",
    "theme.dark": "Dunkel",
    "theme.switchToLight": "Hell",
    "theme.switchToDark": "Dunkel",
    "summary.activeProfiles": "Aktive Profile",
    "summary.newListings": "Neue Listings",
    "summary.watchlist": "Watchlist",
    "summary.hidden": "Ausgeblendet",
    "summary.notified": "Benachrichtigt",
    "summary.runErrors": "Run-Fehler",
    "dashboard.recentRuns": "Letzte Runs",
    "dashboard.recentRunsSubtitle": "Letzte Quellenprüfungen und Connector-Status.",
    "dashboard.clearErrors": "Run-Fehler leeren",
    "dashboard.deleteError": "Fehler löschen",
    "dashboard.sources": "Quellen",
    "dashboard.sourcesSubtitle": "Jobs und gefundene Listings je Marktplatz.",
    "profiles.title": "Jobs",
    "profiles.subtitle": "Gespeicherte Marketplace-Jobs nach Quelle gruppiert.",
    "profiles.editorSubtitle": "Job aus Provider-URL erstellen, dann Filter und Benachrichtigungen ergänzen.",
    "profiles.guidedSetup": "Schnelljob",
    "profiles.quickJob": "Schnelljob",
    "profiles.manual": "Neuer Job",
    "profiles.newJob": "Neuer Job",
    "profiles.all": "Alle Profile",
    "profile.new": "Neuer Job",
    "profile.edit": "Job bearbeiten",
    "profile.searchTitle": "Job",
    "profile.searchSubtitle": "So benennen, dass er später schnell erkennbar ist",
    "profile.name": "Job-Name",
    "profile.source": "Quelle",
    "profile.sourceTitle": "Provider",
    "profile.sourceSubtitle": "Marketplace auswählen und sortierte Such-URL einfügen.",
    "profile.searchUrl": "Such-URL",
    "profile.urlParameters": "URL-Parameter",
    "profile.urlQuery": "Suche",
    "profile.urlCategory": "Kategorie",
    "profile.urlLocation": "Ort",
    "urlParams.key": "Parameter",
    "urlParams.value": "Wert",
    "urlParams.apply": "Übernehmen",
    "urlParams.add": "Parameter hinzufügen",
    "urlParams.remove": "Parameter entfernen",
    "profile.openSource": "Quelle öffnen",
    "profile.filtersTitle": "Kriterien",
    "profile.filtersSubtitle": "Lokale Filter nach dem Abruf der Suchseite",
    "profile.locationHint": "Ortshinweis",
    "profile.minPrice": "Mindestpreis",
    "profile.maxPrice": "Maximalpreis",
    "profile.minPriceShort": "Min.",
    "profile.maxPriceShort": "Max.",
    "profile.pollInterval": "Abrufintervall",
    "profile.keywordTitle": "Keyword-Regeln",
    "profile.keywordSubtitle": "Begriffe matchen, erzwingen oder ausblenden",
    "profile.include": "Einschließen",
    "profile.required": "Erforderlich",
    "profile.exclude": "Ausschließen",
    "profile.hiddenCategories": "Ausgeblendete Kategorien",
    "keyword.add": "Keyword hinzufügen",
    "keyword.remove": "{item} entfernen",
    "filter.ruleType": "Regel",
    "filter.typeRequired": "Nur anzeigen, wenn Text enthält",
    "filter.typeExclude": "Ausblenden, wenn Text enthält",
    "filter.typeInclude": "Bevorzugen, wenn Text enthält",
    "filter.term": "Wort oder Satz",
    "filter.termPlaceholder": "wäsche",
    "filter.add": "Regel hinzufügen",
    "filter.empty": "Noch keine Keyword-Regeln",
    "filter.requiredRule": "Nur anzeigen, wenn Titel oder Beschreibung \"{term}\" enthält",
    "filter.excludeRule": "Ausblenden, wenn Titel oder Beschreibung \"{term}\" enthält",
    "filter.includeRule": "Bevorzugen, wenn Titel oder Beschreibung \"{term}\" enthält",
    "profile.automationTitle": "Automation & Benachrichtigungen",
    "profile.automationSubtitle": "Festlegen, ob der Job im Hintergrund läuft und Benachrichtigungen sendet.",
    "profile.enabled": "aktiv",
    "profile.paused": "pausiert",
    "profile.everyMinutes": "alle {minutes} Min.",
    "profile.maxAge": "Älteste Anzeige",
    "profile.maxAgeShort": "Max. Alter",
    "profile.maxAgeDays": "{days} Tage",
    "profile.save": "Job speichern",
    "profile.runNow": "Jetzt ausführen",
    "wizard.title": "Schnelljob",
    "wizard.subtitle": "Ich führe dich durch Quelle, Suche, Filter und Automation.",
    "wizard.aiPrompt": "Suche in einem Satz beschreiben",
    "wizard.aiCreate": "Mit KI erstellen",
    "wizard.stepSource": "Quelle",
    "wizard.stepSearch": "Suche",
    "wizard.stepFilters": "Filter",
    "wizard.stepReview": "Prüfen",
    "wizard.sourcePrompt": "Wo soll ich suchen?",
    "wizard.sourceHelp": "Wähle den Marktplatz und optional eine Kategorie.",
    "wizard.searchPrompt": "Was soll der Job finden?",
    "wizard.searchHelp": "Beschreibe den Artikel wie bei einer Suche und ergänze optional Preis und Ort.",
    "wizard.filterPrompt": "Was soll bevorzugt oder ignoriert werden?",
    "wizard.filterHelp": "Füge Wörter hinzu, die vorkommen müssen oder ein Listing ausblenden sollen.",
    "wizard.reviewPrompt": "Wie soll der Job laufen?",
    "wizard.reviewHelp": "Lege fest, ob der Job automatisch läuft und Benachrichtigungen sendet.",
    "wizard.summaryTitle": "Job-Vorschau",
    "wizard.summaryEmpty": "Gib einen Suchbegriff ein, dann setze ich den Job zusammen.",
    "wizard.back": "Zurück",
    "wizard.next": "Weiter",
    "wizard.query": "Was soll gefunden werden?",
    "wizard.source": "Quelle",
    "wizard.category": "Kategorie",
    "wizard.allCategories": "Alle Kategorien",
    "wizard.maxPrice": "Maximalpreis",
    "wizard.maxAge": "Älteste Anzeige",
    "wizard.location": "Ort",
    "location.textMode": "PLZ / Ort",
    "location.mapMode": "Karte",
    "location.query": "PLZ oder Ort",
    "location.radius": "Radius",
    "location.wholePlace": "Ganzer Ort",
    "location.coordinates": "Koordinaten",
    "location.resolvedPlace": "Erkannter Ort",
    "location.resolving": "Ort wird ermittelt...",
    "location.mapHint": "In die Karte klicken, um einen ungefähren Mittelpunkt zu setzen",
    "location.help": "Nutze PLZ/Ort wie bei Kleinanzeigen oder klicke einen Kartenpunkt und wähle einen Radius.",
    "location.mapPrefix": "Kartenpunkt",
    "wizard.mustInclude": "Muss enthalten",
    "wizard.hideWords": "Wörter ausblenden",
    "wizard.create": "Job erstellen",
    "wizard.manualForm": "Manuelles Formular",
    "listingTypes.title": "Anzeigenarten",
    "listingTypes.offers": "Angebote",
    "listingTypes.wanted": "Gesuche",
    "listingTypes.help": "Beide ausgewählt bedeutet alle Anzeigenarten.",
    "listingTypes.all": "Alle Anzeigenarten",
    "listingTypes.offersOnly": "Nur Angebote",
    "listingTypes.wantedOnly": "Nur Gesuche",
    "form.backgroundPolling": "Automatisch abrufen",
    "form.telegram": "Telegram",
    "form.webhook": "Webhook",
    "form.telegramNotifications": "Telegram-Benachrichtigungen",
    "form.webhookNotifications": "Webhook-Benachrichtigungen",
    "notifications.pollingHint": "Diesen Job automatisch ausführen.",
    "notifications.telegramHint": "Neue Treffer an Telegram senden.",
    "notifications.webhookHint": "Neue Treffer an deinen Webhook senden.",
    "source.kleinanzeigenHelp": "Öffentliche Kleinanzeigen-Such-URL einfügen.",
    "source.facebookHelp": "Marketplace-Suche oder Kategorie-URL einfügen. Die Facebook-Anleitung in den Einstellungen hilft bei Browser-Sessions.",
    "source.mobiledeHelp": "Öffentliche mobile.de-Suchergebnis-URL einfügen.",
    "source.marktplaatsHelp": "Öffentliche Marktplaats.nl-Suchergebnis-URL einfügen.",
    "source.generic": "Generic HTML",
    "source.genericHelp": "Einfache Listing-Ergebnisseite verwenden.",
    "jobSummary.nameMissing": "Name fehlt",
    "jobSummary.urlMissing": "URL fehlt",
    "jobSummary.provider": "Provider",
    "jobSummary.interval": "{minutes} Min.",
    "jobSummary.pollingOn": "Polling an",
    "jobSummary.pollingOff": "Polling aus",
    "jobSummary.telegramOn": "Telegram an",
    "jobSummary.telegramOff": "Telegram aus",
    "jobSummary.webhookOn": "Webhook an",
    "jobSummary.webhookOff": "Webhook aus",
    "listings.title": "Listings durchsuchen",
    "listings.subtitle": "Scrollen, filtern, zwischen Liste und Kacheln wechseln oder Original öffnen.",
    "listings.settings": "Filter und Anzeige",
    "listings.searchPlaceholder": "Titel, Ort, Kategorie suchen",
    "listings.allStatuses": "Alle Status",
    "listings.includeHidden": "Ausgeblendete/Gesehene anzeigen",
    "listings.runSelectedJob": "Job starten",
    "listings.runSelectedJobHint": "Wähle einen Job aus, um ihn hier zu starten.",
    "listings.resultSummary": "{total} Treffer mit aktuellen Filtern",
    "watchlist.title": "Watchlist",
    "watchlist.subtitle": "Gespeicherte Listings zum Vergleichen oder späteren Öffnen.",
    "review.title": "Swipen",
    "review.subtitle": "Ein Listing nach dem anderen mit Bild, Preis, Anzeigendatum, PLZ, Ort und Quelle prüfen.",
    "review.empty": "Keine Listings zum Prüfen",
    "review.emptyHint": "Starte einen Job oder setze gesehene Listings zurück, um die Queue zu füllen.",
    "review.watch": "Watchlist",
    "review.seen": "Gesehen",
    "review.open": "Original öffnen",
    "review.doubleClick": "Doppelklick speichert in die Watchlist",
    "review.swipe": "Wischen markiert als gesehen",
    "review.reason": "Treffer-Score {score}",
    "status.new": "Neu",
    "status.notified": "Benachrichtigt",
    "status.hidden": "Ausgeblendet",
    "status.seen": "Gesehen",
    "sort.dateDesc": "Neueste zuerst",
    "sort.priceAsc": "Preis niedrig-hoch",
    "sort.priceDesc": "Preis hoch-niedrig",
    "sort.scoreDesc": "Bester Score",
    "view.list": "Liste",
    "view.scan": "Scan",
    "view.tiles": "Kacheln",
    "pagination.pageSize": "Pro Seite",
    "pagination.prev": "Zurück",
    "pagination.next": "Weiter",
    "pagination.range": "{start}-{end} / {total}",
    "settings.notifications": "Benachrichtigungen",
    "settings.notificationsSubtitle": "Konfiguriert Zustellkanäle für Job-Treffer und Tests.",
    "settings.adminCategory": "Admin-Einstellungen",
    "settings.accountCategory": "Konto",
    "settings.telegram": "Telegram",
    "settings.telegramHint": "Bot-Nachrichten an den konfigurierten Chat.",
    "settings.webhook": "Webhook",
    "settings.webhookHint": "HTTP-Zustellung an deinen konfigurierten Empfänger.",
    "settings.deliveryRules": "Zustellregeln",
    "settings.deliveryRulesHint": "Job-Karten legen fest, ob Telegram und Webhook neue Treffer erhalten.",
    "settings.perJob": "pro Job",
    "settings.facebookShort": "Facebook",
    "settings.aiShort": "KI",
    "settings.usersShort": "User",
    "settings.botToken": "Bot-Token",
    "settings.chatId": "Chat-ID",
    "settings.webhookUrl": "Webhook-URL",
    "settings.rateLimit": "Globales Rate-Limit in Sekunden",
    "settings.watchlists": "Watchlists",
    "settings.watchlistsSubtitle": "Wähle die Standardliste, die der normale Merken-Klick nutzt.",
    "settings.defaultWatchlist": "Standard-Watchlist",
    "settings.newWatchlist": "Neue Watchlist",
    "settings.createWatchlist": "Liste anlegen",
    "settings.ai": "KI-Funktionen",
    "settings.aiSubtitle": "Erzeugt Käufernachrichten und Schnelljob-Suchentwürfe, sobald ein Provider konfiguriert ist.",
    "settings.aiEnabled": "KI-Funktionen aktivieren",
    "settings.aiAssessmentsEnabled": "KI-Einschätzungen bei Anzeigen zeigen",
    "settings.aiAssessmentsAutoEnabled": "Sichtbare Anzeigen automatisch einschätzen",
    "settings.aiAssessmentsNewEnabled": "Neue Listings beim Job-Lauf einschätzen",
    "settings.aiAssessmentCostWarning": "KI-Einschätzungen senden Titel, Preis, Beschreibung und Treffer-Daten an den konfigurierten Anbieter. Automatik für neue oder sichtbare Listings kann viele Tokens verbrauchen.",
    "settings.aiTest": "KI testen",
    "settings.aiProvider": "Provider",
    "settings.aiApiKey": "API-Key",
    "settings.aiBaseUrl": "Base-URL",
    "settings.aiModel": "Modell",
    "settings.aiTone": "Tonfall",
    "settings.aiTonePolite": "Sehr höflich",
    "settings.aiToneNormal": "Normal",
    "settings.aiToneCheeky": "Frech",
    "settings.facebook": "Facebook-Marketplace-Session",
    "settings.facebookSubtitle": "Nutze zuerst eine Marketplace-URL. Füge deinen Browser-Cookie nur ein, wenn Facebook den Serverzugriff blockiert.",
    "settings.facebookGuideTitle": "Einrichtungsanleitung",
    "settings.facebookGuideStep1": "Öffne Facebook Marketplace im Browser und stelle Suche, Kategorie, Ort und Filter genau so ein, wie der Job laufen soll.",
    "settings.facebookGuideStep2": "Kopiere die Browser-Adresse und füge sie in einen neuen Facebook-Job ein. Teste einmal „Jetzt ausführen“, bevor du Cookies einträgst.",
    "settings.facebookGuideStep3": "Nur wenn der Lauf eine eingeloggte Facebook-Session verlangt: öffne die Browser-Entwicklertools, kopiere den Cookie-Wert oder die Cookie:-Request-Zeile aus deiner eigenen Marketplace-Anfrage und füge sie unten ein. Der Cookie muss c_user und xs enthalten.",
    "settings.facebookGuideStep4": "Cookies bleiben lokal, können ablaufen und lassen sich durch einen frischen Cookie ersetzen. MarketPlaceLens speichert kein Facebook-Passwort und umgeht keine Logins/CAPTCHAs.",
    "settings.facebookOpen": "Marketplace öffnen",
    "settings.facebookCookie": "Cookie-Header",
    "settings.facebookCookieHint": "Nur mit deinem eigenen Account/deiner eigenen Session nutzen. Füge einen Cookie mit c_user und xs, eine Cookie:-Zeile oder einen kompletten Browser-Request-Header-Block ein. ******** unverändert lassen, um den gespeicherten Cookie zu behalten.",
    "settings.save": "Einstellungen speichern",
    "settings.sendTest": "Test senden",
    "settings.sendWebhookTest": "Webhook-Test senden",
    "settings.password": "Passwort",
    "settings.passwordSubtitle": "Dein lokales Passwort für diese App ändern.",
    "settings.profile": "Persönliche Daten",
    "settings.profileSubtitle": "Wird für KI-Anfragetexte zu deinen Listings verwendet.",
    "settings.displayName": "Name",
    "settings.buyerLocation": "Dein Ort",
    "settings.contactHint": "Kontakt-/Texthinweis",
    "settings.inquirySignature": "Nachrichten-Signatur",
    "settings.saveProfile": "Daten speichern",
    "settings.currentPassword": "Aktuelles Passwort",
    "settings.newPassword": "Neues Passwort",
    "settings.repeatPassword": "Neues Passwort wiederholen",
    "settings.changePassword": "Passwort ändern",
    "settings.users": "User & Rollen",
    "settings.usersSubtitle": "Admins können Konten anlegen und festlegen, wer globale Einstellungen ändern darf.",
    "settings.newUser": "Neuer User",
    "settings.username": "Benutzername",
    "settings.role": "Rolle",
    "settings.roleAdmin": "Admin",
    "settings.roleUser": "User",
    "settings.enabled": "Aktiv",
    "settings.disabled": "Deaktiviert",
    "settings.userPassword": "Initiales Passwort",
    "settings.createUser": "User anlegen",
    "settings.saveUser": "User speichern",
    "settings.deleteUser": "User löschen",
    "settings.editUser": "User bearbeiten",
    "empty.noRuns": "Noch keine Runs",
    "empty.noRunsHint": "Erstelle ein Profil und starte es manuell.",
    "empty.noProfiles": "Keine Profile",
    "empty.noProfilesHint": "Lege rechts die erste Such-URL an.",
    "empty.sourceProfiles": "Noch keine {source}-Jobs",
    "empty.noListings": "Keine Listings",
    "empty.noListingsHint": "Filter anpassen oder Profil ausführen.",
    "empty.noWatchlist": "Keine Watchlist-Listings",
    "empty.noWatchlistHint": "Speichere Listings über den Stern-Button hier.",
    "listing.noImage": "Kein Bild verfügbar",
    "listing.noPrice": "kein Preis",
    "listing.noLocation": "kein Ort",
    "listing.map": "Karte",
    "listing.locationMapTitle": "Anzeigenort",
    "listing.locationMapOpen": "In OpenStreetMap öffnen",
    "listing.locationMapLoading": "Karte wird geladen...",
    "listing.locationMapUnavailable": "Für diesen Ort wurde keine Kartenposition gefunden.",
    "listing.postedAt": "Anzeige",
    "listing.unknownPostedAt": "unbekannt",
    "listing.postcode": "PLZ",
    "listing.place": "Ort",
    "listing.score": "Score {score}",
    "listing.addWatchlist": "Merken",
    "listing.removeWatchlist": "Entfernen",
    "listing.watchMenu": "Watchlist auswählen",
    "listing.newWatchlistPrompt": "Name der neuen Watchlist",
    "listing.addToWatchlist": "Zu {name} hinzufügen",
    "listing.aiInquiry": "KI-Text",
    "listing.aiAssessment": "KI-Einschätzung",
    "listing.aiAssessmentEmpty": "Noch keine KI-Einschätzung.",
    "listing.contacted": "Angeschrieben",
    "listing.notContacted": "Nicht angeschrieben",
    "listing.markContacted": "Angeschrieben",
    "listing.unmarkContacted": "Zurücknehmen",
    "availability.active": "Aktiv",
    "availability.reserved": "Reserviert",
    "availability.deleted": "Gelöscht",
    "availability.unknown": "Nicht geprüft",
    "listing.seen": "Gesehen",
    "listing.hide": "Ausblenden",
    "listing.new": "Neu",
    "date.never": "nie",
    "toast.listingHidden": "Listing ausgeblendet",
    "toast.listingSeen": "Listing als gesehen markiert",
    "toast.listingNew": "Listing wieder auf neu gesetzt",
    "toast.contactedChanged": "Angeschrieben-Status aktualisiert",
    "toast.watchlistAdded": "Zur Watchlist hinzugefügt",
    "toast.watchlistAddedTo": "Zu {name} hinzugefügt",
    "toast.watchlistCreated": "Watchlist angelegt",
    "toast.watchlistRemoved": "Aus Watchlist entfernt",
    "toast.inquiryGenerated": "Anfragetext erstellt",
    "toast.assessmentGenerated": "KI-Einschätzung gespeichert",
    "toast.searchDraftCreated": "Suchentwurf erstellt",
    "toast.aiTestOk": "KI-Anbieter hat geantwortet",
    "toast.inquiryCopied": "Anfrage kopiert",
    "inquiry.title": "KI-Anfragetext",
    "inquiry.copy": "Kopieren",
    "inquiry.close": "Schließen",
    "toast.passwordMismatch": "Neue Passwörter stimmen nicht überein",
    "toast.passwordChanged": "Passwort geändert",
    "toast.userSaved": "User gespeichert",
    "toast.userDeleted": "User gelöscht",
    "toast.profileSaved": "Profil gespeichert",
    "toast.saveProfileFirst": "Speichere zuerst ein Profil",
    "toast.selectJobFirst": "Wähle zuerst einen Job aus",
    "toast.runStarted": "Run gestartet",
    "toast.runComplete": "Run fertig: {new} neu, {hidden} ausgeblendet, {duplicates} Duplikate",
    "toast.runErrorDeleted": "Run-Fehler gelöscht",
    "toast.runErrorsCleared": "{deleted} Run-Fehler geleert",
    "toast.profileDeleted": "Profil gelöscht",
    "toast.searchRequired": "Suchbegriff ist erforderlich",
    "toast.facebookUrlRequired": "Facebook Marketplace braucht eine erreichbare Marketplace-URL.",
    "toast.facebookSearchQueryRequired": "Facebook-Marketplace-Such-URLs brauchen einen Suchbegriff.",
    "toast.listingTypeRequired": "Wähle mindestens eine Kleinanzeigen-Anzeigenart aus",
    "toast.settingsSaved": "Einstellungen gespeichert",
    "toast.profileSaved": "Persönliche Daten gespeichert",
    "toast.telegramSent": "Telegram-Test gesendet",
    "toast.webhookSent": "Webhook-Test gesendet",
    "toast.openCheckStarted": "Aktive Jobs werden jetzt geprüft",
  },
};

const providerCategories = {
  kleinanzeigen: [
    { label: "Auto, Rad & Boot", path: "autos", id: "216" },
    { label: "Autoteile & Reifen", path: "autoteile-reifen", id: "223" },
    { label: "Dienstleistungen", path: "dienstleistungen", id: "297" },
    { label: "Elektronik", path: "elektronik", id: "161" },
    { label: "Elektronik > Notebooks", path: "notebooks", id: "278", aliases: ["laptop", "laptops", "notebook", "notebooks", "macbook"] },
    { label: "Familie, Kind & Baby", path: "familie-kind-baby", id: "17" },
    { label: "Freizeit, Hobby & Nachbarschaft", path: "freizeit-nachbarschaft", id: "185" },
    { label: "Haus & Garten", path: "haus-garten", id: "80" },
    { label: "Haustiere", path: "haustiere", id: "130" },
    { label: "Immobilien", path: "immobilien", id: "195" },
    { label: "Jobs", path: "jobs", id: "102" },
    { label: "Mode & Beauty", path: "mode-beauty", id: "153" },
    { label: "Musik, Filme & Bücher", path: "musik-filme-buecher", id: "73" },
    { label: "Unterricht & Kurse", path: "unterricht-kurse", id: "18" },
    { label: "Verschenken & Tauschen", path: "verschenken-tauschen", id: "192" },
  ],
  facebook: [
    { label: "Vehicles", slug: "vehicles" },
    { label: "Property rentals", slug: "propertyrentals" },
    { label: "Apparel", slug: "apparel" },
    { label: "Classifieds", slug: "classifieds" },
    { label: "Electronics", slug: "electronics" },
    { label: "Entertainment", slug: "entertainment" },
    { label: "Family", slug: "family" },
    { label: "Free stuff", slug: "free" },
    { label: "Garden & outdoor", slug: "garden" },
    { label: "Hobbies", slug: "hobbies" },
    { label: "Home goods", slug: "home" },
    { label: "Home improvement supplies", slug: "homeimprovement" },
    { label: "Musical instruments", slug: "musicalinstruments" },
    { label: "Office supplies", slug: "officesupplies" },
    { label: "Pet supplies", slug: "petsupplies" },
    { label: "Sporting goods", slug: "sportinggoods" },
    { label: "Toys & games", slug: "toys" },
    { label: "Books, movies & music", slug: "bookmoviesmusic" },
  ],
  mobilede: [
    { label: "Cars", path: "fahrzeuge/auto/search.html" },
    { label: "Used cars", path: "auto/gebrauchtwagen.html" },
  ],
  marktplaats: [
    { label: "Cars", path: "autos" },
    { label: "Bicycles", path: "fietsen-en-brommers/fietsen" },
    { label: "Electronics", path: "elektronica" },
    { label: "Home and interior", path: "huis-en-inrichting" },
    { label: "Garden and terrace", path: "tuin-en-terras" },
    { label: "Books", path: "boeken" },
    { label: "Music and instruments", path: "muziek-en-instrumenten" },
    { label: "Games and consoles", path: "spelcomputers-en-games" },
  ],
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

document.addEventListener("DOMContentLoaded", () => {
  applyTheme();
  document.body.dataset.currentView = state.currentView;
  bindNavigation();
  bindForms();
  syncPreferenceControls();
  syncPageSizeControls();
  applyTranslations();
  setupChipInputs();
  updateWizardCategories();
  $("#view-title").textContent = t("nav.dashboard");
  refreshAll().then(triggerAppOpenCheck).catch((error) => toast(errorMessage(error)));
});

function bindNavigation() {
  $$(".nav-item").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
  });
  $("#refresh-button").addEventListener("click", refreshAll);
  $("#logout-button").addEventListener("click", logout);
  $$("[data-settings-tab]").forEach((button) => {
    button.addEventListener("click", () => setSettingsTab(button.dataset.settingsTab));
  });
  $("#language-select").addEventListener("change", () => setLanguage($("#language-select").value));
  $("#theme-toggle").addEventListener("click", () => setTheme(state.theme === "dark" ? "light" : "dark"));
  $("#wizard-button").addEventListener("click", () => showWizard(true));
  $("#wizard-cancel-button").addEventListener("click", () => showWizard(false));
  $("#wizard-back-button").addEventListener("click", previousWizardStep);
  $("#wizard-next-button").addEventListener("click", nextWizardStep);
  $("#wizard-ai-button").addEventListener("click", createWizardDraftWithAi);
  $$("[data-wizard-jump]").forEach((button) => {
    button.addEventListener("click", () => jumpWizardStep(Number(button.dataset.wizardJump)));
  });
  $("#wizard-source").addEventListener("change", () => {
    updateWizardCategories();
    updateWizardSummary();
  });
  $("#wizard-category").addEventListener("change", updateWizardSummary);
  $("#new-profile-button").addEventListener("click", () => editProfile(null));
  $("#profile-source").addEventListener("change", updateSourcePlaceholder);
  $("#profile-url").addEventListener("input", debounce(() => syncProfileParametersFromUrl(false), 220));
  $("#profile-url").addEventListener("change", () => syncProfileParametersFromUrl(true));
  $("#open-source-button").addEventListener("click", openSelectedSource);
  $$("[data-source-option]").forEach((button) => {
    button.addEventListener("click", () => selectSource(button.dataset.sourceOption));
  });
  $$("input[name='wizard-kleinanzeigen-type']").forEach((input) => {
    input.addEventListener("change", () => {
      updateKleinanzeigenTypeVisibility();
      updateWizardSummary();
    });
  });
  [
    "#wizard-query",
    "#wizard-max-price",
    "#wizard-max-age",
    "#wizard-location",
    "#wizard-location-radius",
    "#wizard-required",
    "#wizard-exclude",
    "#wizard-enabled",
    "#wizard-notify",
    "#wizard-notify-webhook",
  ].forEach((selector) => $(selector).addEventListener("input", updateWizardSummary));
  $$("input[name='profile-kleinanzeigen-type']").forEach((input) => {
    input.addEventListener("change", () => {
      syncProfileKleinanzeigenTypeUrl();
      updateFilterPreview();
    });
  });
  $$("[data-location-mode]").forEach((button) => {
    button.addEventListener("click", () => setLocationMode(button.dataset.locationMode));
  });
  ["#profile-location-query", "#profile-location-radius", "#profile-map-radius"].forEach((selector) => {
    $(selector).addEventListener("input", () => {
      syncLocationCriteria();
      updateMapRadiusVisualization();
    });
  });
  $("#profile-location-map").addEventListener("click", setMapLocation);
  $("#run-profile-button").addEventListener("click", runSelectedProfile);
  $("#delete-profile-button").addEventListener("click", deleteSelectedProfile);
  $("#review-watch-button").addEventListener("click", reviewWatchCurrent);
  $("#review-watch-menu-button").addEventListener("click", toggleReviewWatchMenu);
  $("#review-seen-button").addEventListener("click", reviewSeenCurrent);
  $("#review-inquiry-button").addEventListener("click", reviewInquiryCurrent);
  $("#review-open-button").addEventListener("click", reviewOpenCurrent);
  $("#close-listing-map").addEventListener("click", () => $("#listing-map-dialog").close());
  $("#listing-status-filter").addEventListener("change", resetListingsPage);
  $("#listing-profile-filter").addEventListener("change", () => {
    updateListingRunButton();
    resetListingsPage();
  });
  $("#run-listing-profile-button").addEventListener("click", runListingProfile);
  $("#listing-search-filter").addEventListener("input", debounce(resetListingsPage, 220));
  $("#listing-min-price-filter").addEventListener("input", debounce(resetListingsPage, 220));
  $("#listing-max-price-filter").addEventListener("input", debounce(resetListingsPage, 220));
  $("#listing-sort-filter").addEventListener("change", resetListingsPage);
  $("#include-hidden").addEventListener("change", resetListingsPage);
  $("#listing-refresh-button").addEventListener("click", refreshAll);
  $("#listing-scan-button").addEventListener("click", () => showView("review"));
  $$("[data-listing-view]").forEach((button) => {
    button.addEventListener("click", () => setListingView(button.dataset.listingView));
  });
  $$(".pagination-controls").forEach((control) => {
    const watchlistedOnly = control.id === "watchlist-pagination";
    control.querySelector("[data-page-size]").addEventListener("change", (event) => setPageSize(event.target.value));
    control.querySelector("[data-page-prev]").addEventListener("click", () => changePage(watchlistedOnly, -1));
    control.querySelector("[data-page-next]").addEventListener("click", () => changePage(watchlistedOnly, 1));
  });
  [
    "#profile-name",
    "#profile-url",
    "#profile-interval",
    "#profile-min-price",
    "#profile-max-price",
    "#profile-max-age",
    "#profile-include",
    "#profile-required",
    "#profile-exclude",
    "#profile-categories",
    "#profile-enabled",
    "#profile-notify",
    "#profile-notify-webhook",
  ].forEach((selector) => $(selector).addEventListener("input", updateFilterPreview));
}

function bindForms() {
  $("#profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await saveProfile();
    } catch (error) {
      toast(errorMessage(error));
    }
  });
  $("#profile-wizard").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await createProfileFromWizard();
    } catch (error) {
      toast(errorMessage(error));
    }
  });
  $("#settings-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveSettings();
  });
  $("#ai-settings-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveSettings();
  });
  $("#facebook-settings-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveSettings();
  });
  $("#user-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveUser();
  });
  $("#new-user-button").addEventListener("click", () => editUser(null));
  $("#delete-user-button").addEventListener("click", deleteSelectedUser);
  $("#watchlist-settings-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await createWatchlistFromSettings();
  });
  $("#default-watchlist").addEventListener("change", saveSettings);
  $("#ai-provider").addEventListener("change", updateAiProviderHints);
  $("#copy-inquiry-button").addEventListener("click", copyInquiryText);
  $("#password-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await changePassword();
  });
  $("#account-profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveAccountProfile();
  });
  $("#add-filter-rule-button").addEventListener("click", addGuidedFilterRule);
  $("#filter-rule-term").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addGuidedFilterRule();
    }
  });
  $("#telegram-test-button").addEventListener("click", testTelegram);
  $("#webhook-test-button").addEventListener("click", testWebhook);
  $("#ai-test-button").addEventListener("click", testAiProvider);
  $("#dashboard-clear-run-errors").addEventListener("click", clearRunErrors);
  $("#settings-clear-run-errors").addEventListener("click", clearRunErrors);
}

function showView(view) {
  state.currentView = view;
  document.body.dataset.currentView = view;
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === view));
  $$(".view").forEach((item) => item.classList.toggle("active", item.id === `${view}-view`));
  $("#view-title").textContent = t({
    dashboard: "nav.dashboard",
    profiles: "nav.profiles",
    listings: "nav.listings",
    review: "nav.review",
    watchlist: "nav.watchlist",
    settings: "nav.settings",
  }[view]);
  if (view === "listings") loadListings();
  if (view === "watchlist") loadWatchlist();
}

function showWizard(visible) {
  $("#profile-wizard").classList.toggle("hidden", !visible);
  $("#profile-form").classList.toggle("hidden", visible);
  if (visible) {
    updateProfileFormTitle(true);
    updateWizardCategories();
    setWizardStep(0);
    updateWizardSummary();
    focusWizardStep();
  } else {
    editProfile(null);
  }
}

function setWizardStep(step) {
  state.wizardStep = Math.max(0, Math.min(3, step));
  $$("[data-wizard-step]").forEach((panel) => {
    panel.classList.toggle("active", Number(panel.dataset.wizardStep) === state.wizardStep);
  });
  $$("[data-wizard-jump]").forEach((button) => {
    const index = Number(button.dataset.wizardJump);
    button.classList.toggle("active", index === state.wizardStep);
    button.classList.toggle("complete", index < state.wizardStep);
  });
  $("#wizard-back-button").disabled = state.wizardStep === 0;
  $("#wizard-next-button").classList.toggle("hidden", state.wizardStep === 3);
  $("#wizard-create-button").classList.toggle("hidden", state.wizardStep !== 3);
  updateWizardSummary();
}

function nextWizardStep() {
  if (!validateWizardStep(state.wizardStep)) return;
  setWizardStep(state.wizardStep + 1);
  focusWizardStep();
}

function previousWizardStep() {
  setWizardStep(state.wizardStep - 1);
  focusWizardStep();
}

function jumpWizardStep(step) {
  for (let index = 0; index < step; index += 1) {
    if (!validateWizardStep(index)) {
      setWizardStep(index);
      focusWizardStep();
      return;
    }
  }
  setWizardStep(step);
  focusWizardStep();
}

function focusWizardStep() {
  const active = $(`[data-wizard-step="${state.wizardStep}"]`);
  const field = active?.querySelector("input:not([type='checkbox']), select, textarea");
  if (field) field.focus();
}

function validateWizardStep(step) {
  if (step === 0 && $("#wizard-source").value === "kleinanzeigen" && !selectedKleinanzeigenTypes("wizard").length) {
    toast(t("toast.listingTypeRequired"));
    return false;
  }
  if (step === 1 && !$("#wizard-query").value.trim()) {
    toast(t("toast.searchRequired"));
    return false;
  }
  return true;
}

async function refreshAll() {
  try {
    await loadAuthStatus();
    await Promise.all([loadVersion(), loadSummary(), loadProfiles(), loadListings(), loadWatchlist(), loadReviewQueue(), loadSettings(), loadAccountProfile(), loadUsers()]);
  } catch (error) {
    if (String(error.message).includes("Not authenticated") || String(error.message).includes("401")) {
      window.location.href = "/login";
      return;
    }
    throw error;
  }
}

async function loadVersion() {
  const version = await api("/api/version");
  state.version = version;
  const label = version.build_code || version.version || "";
  $("#app-version").textContent = label;
  $("#floating-app-version").textContent = label;
}

async function loadAuthStatus() {
  const status = await api("/api/auth/status");
  state.currentUser = status.user || null;
  const admin = isAdmin();
  $$(".admin-only").forEach((node) => node.classList.toggle("hidden", !admin));
  if (!admin && !["watchlists", "account"].includes(state.settingsTab)) state.settingsTab = "watchlists";
  renderSettingsTabs();
}

function isAdmin() {
  return state.currentUser?.role === "admin";
}

function setSettingsTab(tab) {
  const adminTabs = ["notifications", "facebook", "ai", "users", "runs"];
  state.settingsTab = adminTabs.includes(tab) && !isAdmin() ? "account" : tab;
  renderSettingsTabs();
}

function renderSettingsTabs() {
  const adminTabs = ["notifications", "facebook", "ai", "users", "runs"];
  const visibleTabs = isAdmin() ? ["notifications", "facebook", "ai", "watchlists", "users", "runs", "account"] : ["watchlists", "account"];
  const active = visibleTabs.includes(state.settingsTab) ? state.settingsTab : (isAdmin() ? "notifications" : "watchlists");
  state.settingsTab = active;
  $$("[data-settings-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.settingsTab === active);
    button.setAttribute("aria-selected", String(button.dataset.settingsTab === active));
  });
  $$(".settings-panel").forEach((node) => {
    node.classList.toggle("hidden", !node.classList.contains(`settings-panel-${active}`));
  });
}

async function triggerAppOpenCheck() {
  if (state.appOpenCheckStarted) return;
  state.appOpenCheckStarted = true;
  try {
    const result = await api("/api/profiles/open-check", { method: "POST" });
    if (result.started) {
      toast(t("toast.openCheckStarted"));
      setTimeout(refreshAll, 3500);
    }
  } catch {
    state.appOpenCheckStarted = false;
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${await responseErrorMessage(response)}`);
  }
  return response.json();
}

async function responseErrorMessage(response) {
  const text = await response.text();
  if (!text) return response.statusText;
  try {
    const data = JSON.parse(text);
    return data.detail || text;
  } catch {
    return text;
  }
}

async function logout() {
  await api("/api/auth/logout", { method: "POST" });
  window.location.href = "/login";
}

async function loadSummary() {
  const summary = await api("/api/summary");
  $("#summary-active").textContent = `${summary.profiles_enabled}/${summary.profiles_total}`;
  $("#summary-new").textContent = summary.listings_new;
  $("#summary-watchlisted").textContent = summary.listings_watchlisted;
  $("#summary-hidden").textContent = summary.listings_hidden;
  $("#summary-notified").textContent = summary.listings_notified;
  $("#summary-errors").textContent = summary.run_errors;
  const runsHtml = summary.recent_runs.length
    ? summary.recent_runs.map((run) => `
      <article class="${run.status === "error" ? "run-error-card" : ""}">
        <div class="run-log-heading">
          <strong>${escapeHtml(run.profile_name)}</strong>
          ${isAdmin() && run.status === "error" ? `<button class="mini-button danger" type="button" data-run-error-delete="${run.id}">${escapeHtml(t("dashboard.deleteError"))}</button>` : ""}
        </div>
        <p class="meta">${escapeHtml(run.status)} · fetched ${run.fetched} · new ${run.new_count} · hidden ${run.hidden_count} · duplicate ${run.duplicate_count} · ${formatDate(run.finished_at)}</p>
        ${run.error_message ? `<p class="meta danger-text">${escapeHtml(run.error_message)}</p>` : ""}
      </article>
    `).join("")
    : `<article><strong>${escapeHtml(t("empty.noRuns"))}</strong><p class="meta">${escapeHtml(t("empty.noRunsHint"))}</p></article>`;
  $("#recent-runs").innerHTML = runsHtml;
  $("#dashboard-recent-runs").innerHTML = runsHtml;
  bindRunErrorButtons();
  $("#dashboard-sources").innerHTML = (summary.source_counts || []).length
    ? summary.source_counts.map((source) => `
      <article class="source-summary-card">
        <span class="source-badge ${escapeAttribute(source.source_type)}">${escapeHtml(sourceLabel(source.source_type))}</span>
        <strong>${source.profile_count || 0}</strong>
        <p class="meta">${escapeHtml(t("profiles.title"))} · ${source.listing_count || 0} ${escapeHtml(t("nav.listings"))}</p>
      </article>
    `).join("")
    : `<article><strong>${escapeHtml(t("empty.noProfiles"))}</strong><p class="meta">${escapeHtml(t("empty.noProfilesHint"))}</p></article>`;
}

function bindRunErrorButtons() {
  $$("[data-run-error-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteRunError(button.dataset.runErrorDelete));
  });
}

async function deleteRunError(id) {
  if (!id) return;
  await api(`/api/run-logs/${id}`, { method: "DELETE" });
  toast(t("toast.runErrorDeleted"));
  await loadSummary();
}

async function clearRunErrors() {
  const result = await api("/api/run-logs/errors", { method: "DELETE" });
  toast(t("toast.runErrorsCleared", { deleted: result.deleted || 0 }));
  await loadSummary();
}

async function loadProfiles() {
  state.profiles = await api("/api/profiles");
  $("#profiles-list").innerHTML = state.profiles.length
    ? groupedProfilesMarkup(state.profiles)
    : `<article class="profile-card"><h3>${escapeHtml(t("empty.noProfiles"))}</h3><p class="meta">${escapeHtml(t("empty.noProfilesHint"))}</p></article>`;
  $$(".profile-card[data-id]").forEach((card) => {
    card.addEventListener("click", () => {
      const profile = state.profiles.find((item) => item.id === Number(card.dataset.id));
      editProfile(profile);
    });
  });
  const current = $("#listing-profile-filter").value;
  $("#listing-profile-filter").innerHTML = `<option value="">${escapeHtml(t("profiles.all"))}</option>${state.profiles.map((profile) => `
    <option value="${profile.id}">${escapeHtml(profile.name)}</option>
  `).join("")}`;
  $("#listing-profile-filter").value = current;
  updateListingRunButton();
}

function groupedProfilesMarkup(profiles) {
  const order = ["kleinanzeigen", "facebook", "mobilede", "marktplaats", "html"];
  return order.map((source) => {
    const items = profiles.filter((profile) => profile.source_type === source);
    return `
      <section class="profile-source-group">
        <h3>${escapeHtml(sourceLabel(source))}</h3>
        ${items.length ? items.map((profile) => `
      <article class="profile-card ${state.selectedProfile?.id === profile.id ? "active" : ""}" data-id="${profile.id}">
        <div class="profile-card-top">
          <h4>${escapeHtml(profile.name)}</h4>
          <span class="source-badge ${escapeAttribute(profile.source_type)}">${escapeHtml(sourceLabel(profile.source_type))}</span>
        </div>
        <p class="meta">${profile.enabled ? t("profile.enabled") : t("profile.paused")} · ${t("profile.everyMinutes", { minutes: profile.poll_interval_minutes })}</p>
        <p class="meta">${escapeHtml(profile.search_url)}</p>
      </article>
        `).join("") : `<article class="profile-empty">${escapeHtml(t("empty.sourceProfiles", { source: sourceLabel(source) }))}</article>`}
      </section>
    `;
  }).join("");
}

function sourceLabel(source) {
  return {
    kleinanzeigen: "Kleinanzeigen",
    facebook: "Facebook Marketplace (in testing)",
    mobilede: "mobile.de (in testing)",
    marktplaats: "Marktplaats.nl (in testing)",
    html: "Generic HTML",
  }[source] || source;
}

function sourceBaseUrl(source) {
  return sourceBaseUrls()[source] || "";
}

function sourceBaseUrls() {
  return {
    kleinanzeigen: "https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=",
    facebook: "https://www.facebook.com/marketplace/search/?query=",
    mobilede: "https://suchen.mobile.de/fahrzeuge/auto/search.html?ft=",
    marktplaats: "https://www.marktplaats.nl/q/",
    html: "",
  };
}

function selectedKleinanzeigenTypes(scope) {
  return $$(`input[name='${scope}-kleinanzeigen-type']:checked`)
    .map((input) => input.value)
    .filter((value) => ["angebote", "gesuche"].includes(value));
}

function setKleinanzeigenTypes(scope, types) {
  const selected = types?.length ? types : ["angebote", "gesuche"];
  $$(`input[name='${scope}-kleinanzeigen-type']`).forEach((input) => {
    input.checked = selected.includes(input.value);
  });
}

function kleinanzeigenTypesFromUrl(url) {
  const value = String(url || "");
  if (value.includes("anzeige:angebote")) return ["angebote"];
  if (value.includes("anzeige:gesuche")) return ["gesuche"];
  return ["angebote", "gesuche"];
}

function kleinanzeigenTypeLabel(types = selectedKleinanzeigenTypes("profile")) {
  const selected = types.length ? types : ["angebote", "gesuche"];
  if (selected.length === 1 && selected[0] === "angebote") return t("listingTypes.offersOnly");
  if (selected.length === 1 && selected[0] === "gesuche") return t("listingTypes.wantedOnly");
  return t("listingTypes.all");
}

function kleinanzeigenTypeSegment(types) {
  return types.length === 1 ? `/anzeige:${types[0]}` : "";
}

function keywordUrlPath(query) {
  return encodeURIComponent(query.trim()).replace(/%20/g, "-");
}

function setKleinanzeigenTypeInUrl(url, types) {
  const raw = String(url || "").trim();
  if (!raw || !raw.includes("kleinanzeigen.de")) return raw;
  const selected = types.length ? types : ["angebote", "gesuche"];
  let next = raw
    .replace(/\/anzeige:(angebote|gesuche)(?=\/|$)/, "")
    .replace(/\/s-anzeige:(angebote|gesuche)(?=\/|$)/, "/s");
  if (next.includes("/s-suchanfrage.html") || selected.length !== 1) return next;
  const type = selected[0];
  if (/\/s-[^/?#]+/.test(next)) return next.replace(/(\/s-[^/?#]+)/, `$1/anzeige:${type}`);
  if (/\/s(?=\/|$)/.test(next)) return next.replace(/\/s(?=\/|$)/, `/s-anzeige:${type}`);
  return next;
}

function updateKleinanzeigenTypeVisibility() {
  const wizardTypes = $("#wizard-kleinanzeigen-types");
  if (wizardTypes) wizardTypes.classList.toggle("hidden", $("#wizard-source").value !== "kleinanzeigen");
  const profileTypes = $("#profile-kleinanzeigen-types");
  if (profileTypes) profileTypes.classList.toggle("hidden", $("#profile-source").value !== "kleinanzeigen");
}

function syncProfileKleinanzeigenTypeUrl() {
  if ($("#profile-source").value !== "kleinanzeigen") return;
  $("#profile-url").value = setKleinanzeigenTypeInUrl($("#profile-url").value, selectedKleinanzeigenTypes("profile"));
}

function syncProfileKleinanzeigenTypesFromUrl() {
  if ($("#profile-source").value !== "kleinanzeigen") return;
  setKleinanzeigenTypes("profile", kleinanzeigenTypesFromUrl($("#profile-url").value));
  updateFilterPreview();
}

function syncProfileParametersFromUrl(applyFields) {
  const params = parseSearchUrlParameters($("#profile-url").value);
  if (params.source && params.source !== $("#profile-source").value) {
    $("#profile-source").value = params.source;
    updateSourcePlaceholder();
  }
  if (params.source === "kleinanzeigen" && params.types?.length) {
    setKleinanzeigenTypes("profile", params.types);
  }
  if (applyFields) applyUrlParametersToForm(params);
  renderUrlParameterPreview(params);
  updateFilterPreview();
}

function parseSearchUrlParameters(value) {
  const raw = String(value || "").trim();
  if (!raw) return {};
  let url;
  try {
    url = new URL(raw);
  } catch {
    return {};
  }
  const host = url.hostname.toLowerCase();
  if (host.includes("kleinanzeigen.de")) return parseKleinanzeigenUrl(url);
  if (host === "facebook.com" || host.endsWith(".facebook.com")) return parseFacebookMarketplaceUrl(url);
  if (host === "mobile.de" || host.endsWith(".mobile.de")) return parseMobileDeUrl(url);
  if (host === "marktplaats.nl" || host.endsWith(".marktplaats.nl")) return parseMarktplaatsUrl(url);
  return {};
}

function parseKleinanzeigenUrl(url) {
  const segments = url.pathname.split("/").filter(Boolean).map((part) => decodeURIComponent(part));
  const query = url.searchParams.get("keywords") || keywordFromKleinanzeigenSegments(segments);
  const category = categoryFromKleinanzeigenUrl(url.pathname);
  const location = segments.find((part) => /^\d{5}$/.test(part)) || "";
  return {
    source: "kleinanzeigen",
    query: humanizeUrlTerm(query),
    category: category?.label || "",
    location,
    types: kleinanzeigenTypesFromUrl(url.toString()),
  };
}

function parseFacebookMarketplaceUrl(url) {
  const categoryMatch = url.pathname.match(/\/marketplace\/category\/([^/]+)/i);
  const category = categoryMatch
    ? (providerCategories.facebook.find((item) => item.slug === categoryMatch[1])?.label || humanizeUrlTerm(categoryMatch[1]))
    : "";
  return {
    source: "facebook",
    query: humanizeUrlTerm(url.searchParams.get("query") || ""),
    category,
  };
}

function parseMobileDeUrl(url) {
  const category = providerCategories.mobilede.find((item) => url.pathname.includes(item.path))?.label || "";
  return {
    source: "mobilede",
    query: humanizeUrlTerm(url.searchParams.get("ft") || url.searchParams.get("q") || ""),
    category,
  };
}

function parseMarktplaatsUrl(url) {
  const segments = url.pathname.split("/").filter(Boolean).map((part) => decodeURIComponent(part));
  const queryIndex = segments.indexOf("q");
  const query = queryIndex >= 0 ? segments[queryIndex + 1] : url.searchParams.get("query") || url.searchParams.get("q") || "";
  const category = providerCategories.marktplaats.find((item) => url.pathname.includes(`/l/${item.path}/`))?.label || "";
  const location = url.searchParams.get("distanceMeters") ? url.searchParams.get("postcode") || "" : "";
  return {
    source: "marktplaats",
    query: humanizeUrlTerm(query),
    category,
    location,
  };
}

function keywordFromKleinanzeigenSegments(segments) {
  const candidates = segments.filter((part) => {
    return !part.startsWith("s-")
      && !part.startsWith("k0")
      && !/^c\d+/i.test(part)
      && !/^l\d+/i.test(part)
      && !/^r\d+/i.test(part)
      && !part.startsWith("anzeige:")
      && !/^\d{5}$/.test(part);
  });
  return candidates.at(-1) || "";
}

function categoryFromKleinanzeigenUrl(pathname) {
  const categoryId = pathname.match(/c(\d+)/)?.[1];
  if (categoryId) {
    const byId = providerCategories.kleinanzeigen.find((item) => item.id === categoryId);
    if (byId) return byId;
  }
  return providerCategories.kleinanzeigen.find((item) => pathname.includes(`/s-${item.path}`));
}

function humanizeUrlTerm(value) {
  return String(value || "").replace(/[-_]+/g, " ").trim();
}

function applyUrlParametersToForm(params) {
  if (params.query && !$("#profile-include").value.trim()) {
    $("#profile-include").value = params.query.split(/\s+/).filter(Boolean).join("\n");
  }
  if (params.location && !$("#profile-location-query").value.trim()) {
    $("#profile-location-query").value = params.location;
    setLocationMode("text");
  }
  syncAllChipInputs();
}

function renderUrlParameterPreview(params = parseSearchUrlParameters($("#profile-url").value)) {
  const target = $("#url-parameter-preview");
  if (!target) return;
  const url = currentProfileUrl();
  const entries = url ? Array.from(url.searchParams.entries()) : [];
  const hints = [];
  if (params.source) hints.push(`${t("jobSummary.provider")}: ${sourceLabel(params.source)}`);
  if (params.category) hints.push(`${t("profile.urlCategory")}: ${params.category}`);
  if (params.location) hints.push(`${t("profile.urlLocation")}: ${params.location}`);
  target.classList.toggle("hidden", !url && hints.length === 0);
  target.innerHTML = `
    <div class="url-param-header">
      <strong>${escapeHtml(t("profile.urlParameters"))}</strong>
      ${hints.map((hint) => `<span>${escapeHtml(hint)}</span>`).join("")}
    </div>
    <div class="url-param-grid">
      ${entries.map(([key, value]) => urlParameterRow(key, value)).join("")}
      ${entries.length ? "" : urlParameterRow("", "")}
    </div>
    <div class="url-param-actions">
      <button class="mini-button" type="button" data-url-param-add>${escapeHtml(t("urlParams.add"))}</button>
      <button class="mini-button primary" type="button" data-url-param-apply>${escapeHtml(t("urlParams.apply"))}</button>
    </div>
  `;
  target.querySelector("[data-url-param-add]")?.addEventListener("click", () => {
    target.querySelector(".url-param-grid")?.insertAdjacentHTML("beforeend", urlParameterRow("", ""));
    bindUrlParameterRows(target);
  });
  target.querySelector("[data-url-param-apply]")?.addEventListener("click", applyUrlParameterRows);
  bindUrlParameterRows(target);
}

function currentProfileUrl() {
  try {
    return new URL($("#profile-url").value.trim());
  } catch {
    return null;
  }
}

function urlParameterRow(key, value) {
  return `
    <div class="url-param-row">
      <input data-url-param-key aria-label="${escapeAttribute(t("urlParams.key"))}" value="${escapeAttribute(key)}" placeholder="${escapeAttribute(t("urlParams.key"))}">
      <input data-url-param-value aria-label="${escapeAttribute(t("urlParams.value"))}" value="${escapeAttribute(value)}" placeholder="${escapeAttribute(t("urlParams.value"))}">
      <button class="icon-button danger" type="button" data-url-param-remove aria-label="${escapeAttribute(t("urlParams.remove"))}">×</button>
    </div>
  `;
}

function bindUrlParameterRows(target = $("#url-parameter-preview")) {
  target.querySelectorAll("[data-url-param-remove]").forEach((button) => {
    button.onclick = () => button.closest(".url-param-row")?.remove();
  });
}

function applyUrlParameterRows() {
  const url = currentProfileUrl();
  if (!url) return;
  url.search = "";
  $$("#url-parameter-preview .url-param-row").forEach((row) => {
    const key = row.querySelector("[data-url-param-key]")?.value.trim();
    const value = row.querySelector("[data-url-param-value]")?.value.trim();
    if (key) url.searchParams.append(key, value || "");
  });
  $("#profile-url").value = url.toString();
  syncProfileParametersFromUrl(true);
}

function setLocationMode(mode) {
  const selected = mode === "map" ? "map" : "text";
  $$("[data-location-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.locationMode === selected);
  });
  $$("[data-location-panel]").forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.locationPanel !== selected);
  });
  if (selected === "map") {
    initializeLocationMap();
    setTimeout(() => state.locationMap?.invalidateSize(), 80);
  }
  syncLocationCriteria();
}

function currentLocationMode() {
  return $("[data-location-mode].active")?.dataset.locationMode === "map" ? "map" : "text";
}

function radiusLabel(value) {
  return value ? `+${value} km` : t("location.wholePlace");
}

function formatLocationCriteria() {
  const mode = currentLocationMode();
  if (mode === "map") {
    const coordinates = $("#profile-location-coordinates").value.trim();
    if (!coordinates) return "";
    const resolvedPlace = $("#profile-location-label").value.trim();
    return [
      `${t("location.mapPrefix")}: ${coordinates}`,
      resolvedPlace,
      radiusLabel($("#profile-map-radius").value),
    ].filter(Boolean).join(" · ");
  }
  const query = $("#profile-location-query").value.trim();
  if (!query) return "";
  return `${query} · ${radiusLabel($("#profile-location-radius").value)}`;
}

function syncLocationCriteria() {
  $("#profile-location").value = formatLocationCriteria();
  updateFilterPreview();
}

function setMapLocation(event) {
  if (state.locationMap) return;
  const rect = event.currentTarget.getBoundingClientRect();
  const x = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
  const y = Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height));
  const lat = (55.1 - y * 8.0).toFixed(4);
  const lng = (5.9 + x * 9.4).toFixed(4);
  setMapCoordinates(Number(lat), Number(lng));
}

function initializeLocationMap() {
  const node = $("#profile-location-map");
  if (!node || state.locationMap || !window.L) return;
  node.classList.add("leaflet-backed");
  state.locationMap = L.map(node, {
    zoomControl: true,
    scrollWheelZoom: false,
  }).setView([51.1657, 10.4515], 6);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(state.locationMap);
  state.locationMap.on("click", (event) => setMapCoordinates(event.latlng.lat, event.latlng.lng));
  const coordinates = $("#profile-location-coordinates").value.trim();
  const match = coordinates.match(/(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/);
  if (match) updateLeafletMarker(Number(match[1]), Number(match[2]));
}

function setMapCoordinates(lat, lng, options = {}) {
  const formattedLat = Number(lat).toFixed(4);
  const formattedLng = Number(lng).toFixed(4);
  $("#profile-location-coordinates").value = `${formattedLat}, ${formattedLng}`;
  if (state.locationMap) {
    updateLeafletMarker(Number(formattedLat), Number(formattedLng));
  } else {
    updateFallbackMapPin(Number(formattedLat), Number(formattedLng));
  }
  syncLocationCriteria();
  if (options.resolve !== false) {
    resolveMapPoint(Number(formattedLat), Number(formattedLng));
  }
}

async function resolveMapPoint(lat, lng) {
  const token = ++state.locationResolveToken;
  $("#profile-location-label").value = "";
  $("#profile-location-label").placeholder = t("location.resolving");
  syncLocationCriteria();
  try {
    const place = await reverseGeocodeLocation(lat, lng);
    if (token !== state.locationResolveToken) return;
    $("#profile-location-label").value = place;
    $("#profile-location-label").placeholder = "10115 Berlin";
  } catch {
    if (token !== state.locationResolveToken) return;
    $("#profile-location-label").value = "";
    $("#profile-location-label").placeholder = "10115 Berlin";
  }
  syncLocationCriteria();
}

async function reverseGeocodeLocation(lat, lng) {
  const url = new URL("https://nominatim.openstreetmap.org/reverse");
  url.searchParams.set("format", "jsonv2");
  url.searchParams.set("lat", String(lat));
  url.searchParams.set("lon", String(lng));
  url.searchParams.set("zoom", "14");
  url.searchParams.set("addressdetails", "1");
  const response = await fetch(url.toString(), { headers: { "Accept": "application/json" } });
  if (!response.ok) throw new Error("reverse geocoding failed");
  const data = await response.json();
  const address = data.address || {};
  const postcode = address.postcode || "";
  const place = address.city || address.town || address.village || address.municipality || address.suburb || "";
  const resolved = [postcode, place].filter(Boolean).join(" ").trim();
  return resolved || String(data.display_name || "").split(",").slice(0, 2).join(", ").trim();
}

function updateFallbackMapPin(lat, lng) {
  const x = Math.max(0, Math.min(1, (lng - 5.9) / 9.4));
  const y = Math.max(0, Math.min(1, (55.1 - lat) / 8.0));
  const pin = $("#profile-location-pin");
  pin.style.left = `${x * 100}%`;
  pin.style.top = `${y * 100}%`;
  pin.classList.add("visible");
}

function updateLeafletMarker(lat, lng) {
  if (!state.locationMap || !window.L) return;
  const latLng = [lat, lng];
  if (!state.locationMarker) {
    state.locationMarker = L.marker(latLng).addTo(state.locationMap);
  } else {
    state.locationMarker.setLatLng(latLng);
  }
  state.locationMap.setView(latLng, Math.max(state.locationMap.getZoom(), 9));
  updateMapRadiusVisualization();
}

function updateMapRadiusVisualization() {
  if (!state.locationMap || !state.locationMarker || !window.L) return;
  const radiusKm = Number($("#profile-map-radius").value || 0);
  if (!radiusKm) {
    if (state.locationCircle) {
      state.locationMap.removeLayer(state.locationCircle);
      state.locationCircle = null;
    }
    return;
  }
  const options = { color: "#14a085", fillColor: "#14a085", fillOpacity: 0.14, weight: 2 };
  if (!state.locationCircle) {
    state.locationCircle = L.circle(state.locationMarker.getLatLng(), { ...options, radius: radiusKm * 1000 }).addTo(state.locationMap);
  } else {
    state.locationCircle.setLatLng(state.locationMarker.getLatLng());
    state.locationCircle.setRadius(radiusKm * 1000);
  }
}

function clearLeafletMapSelection() {
  if (state.locationCircle && state.locationMap) {
    state.locationMap.removeLayer(state.locationCircle);
    state.locationCircle = null;
  }
  if (state.locationMarker && state.locationMap) {
    state.locationMap.removeLayer(state.locationMarker);
    state.locationMarker = null;
  }
}

function applyLocationCriteria(value) {
  const raw = String(value || "").trim();
  $("#profile-location").value = raw;
  $("#profile-location-query").value = "";
  $("#profile-location-radius").value = "";
  $("#profile-location-coordinates").value = "";
  $("#profile-location-label").value = "";
  $("#profile-map-radius").value = "";
  $("#profile-location-pin").classList.remove("visible");
  clearLeafletMapSelection();

  if (!raw) {
    setLocationMode("text");
    return;
  }
  if (raw.toLowerCase().startsWith("map point:") || raw.toLowerCase().startsWith("kartenpunkt:")) {
    setLocationMode("map");
    const coordinateMatch = raw.match(/(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/);
    if (coordinateMatch) {
      const lat = Number(coordinateMatch[1]);
      const lng = Number(coordinateMatch[2]);
      const resolvedPlace = mapResolvedPlaceFromCriteria(raw);
      $("#profile-location-label").value = resolvedPlace;
      setMapCoordinates(lat, lng, { resolve: !resolvedPlace });
    }
    const radiusMatch = raw.match(/\+(\d+)\s*km/i);
    $("#profile-map-radius").value = radiusMatch?.[1] || "";
    updateMapRadiusVisualization();
    syncLocationCriteria();
    return;
  }
  setLocationMode("text");
  const [queryPart] = raw.split("·");
  $("#profile-location-query").value = queryPart.trim();
  const radiusMatch = raw.match(/\+(\d+)\s*km/i);
  $("#profile-location-radius").value = radiusMatch?.[1] || "";
  syncLocationCriteria();
}

function mapResolvedPlaceFromCriteria(value) {
  return String(value || "")
    .replace(/^(?:map point|kartenpunkt)\s*:/i, "")
    .split("·")
    .map((part) => part.trim())
    .filter((part) => {
      return part
        && !/^[-+]?\d+(?:\.\d+)?\s*,\s*[-+]?\d+(?:\.\d+)?$/.test(part)
        && !/\+?\s*\d+\s*km\b/i.test(part)
        && !/^(whole place|ganzer ort)$/i.test(part);
    })[0] || "";
}

async function changePassword() {
  const current = $("#current-password").value;
  const next = $("#new-password").value;
  const repeated = $("#repeat-password").value;
  if (next !== repeated) return toast(t("toast.passwordMismatch"));
  await api("/api/settings/password", {
    method: "POST",
    body: JSON.stringify({ current_password: current, new_password: next }),
  });
  $("#current-password").value = "";
  $("#new-password").value = "";
  $("#repeat-password").value = "";
  toast(t("toast.passwordChanged"));
}

function editProfile(profile) {
  $("#profile-wizard").classList.add("hidden");
  $("#profile-form").classList.remove("hidden");
  state.selectedProfile = profile;
  updateProfileFormTitle(false);
  $("#profile-id").value = profile?.id || "";
  $("#profile-name").value = profile?.name || "";
  $("#profile-source").value = profile?.source_type || "kleinanzeigen";
  $("#profile-url").value = profile?.search_url || sourceBaseUrl($("#profile-source").value);
  setKleinanzeigenTypes("profile", kleinanzeigenTypesFromUrl(profile?.search_url || ""));
  updateSourcePlaceholder();
  updateSourceOptions();
  syncProfileParametersFromUrl(false);
  $("#profile-interval").value = profile?.poll_interval_minutes || 60;
  applyLocationCriteria(profile?.location_hint || "");
  $("#profile-min-price").value = profile?.min_price ?? "";
  $("#profile-max-price").value = profile?.max_price ?? "";
  $("#profile-max-age").value = profile?.max_listing_age_days || 365;
  $("#profile-include").value = (profile?.include_keywords || []).join("\n");
  $("#profile-required").value = (profile?.required_keywords || []).join("\n");
  $("#profile-exclude").value = (profile?.exclude_keywords || []).join("\n");
  $("#profile-categories").value = (profile?.excluded_categories || []).join("\n");
  syncAllChipInputs();
  renderGuidedFilterRules();
  $("#profile-enabled").checked = profile?.enabled ?? true;
  $("#profile-notify").checked = profile?.notify_telegram ?? true;
  $("#profile-notify-webhook").checked = profile?.notify_webhook ?? false;
  updateKleinanzeigenTypeVisibility();
  updateFilterPreview();
  updateJobSetupSummary();
  loadProfiles();
}

function updateProfileFormTitle(wizardVisible = !$("#profile-wizard").classList.contains("hidden")) {
  $("#profile-form-title").textContent = wizardVisible
    ? t("wizard.title")
    : state.selectedProfile ? t("profile.edit") : t("profile.new");
}

async function createProfileFromWizard() {
  for (let step = 0; step <= 3; step += 1) {
    if (!validateWizardStep(step)) {
      setWizardStep(step);
      focusWizardStep();
      return;
    }
  }
  const query = $("#wizard-query").value.trim();
  if (!query) return toast(t("toast.searchRequired"));
  const source = $("#wizard-source").value;
  const category = selectedWizardCategory();
  const selectedTypes = selectedKleinanzeigenTypes("wizard");
  if (source === "kleinanzeigen" && !selectedTypes.length) return toast(t("toast.listingTypeRequired"));
  $("#profile-id").value = "";
  $("#profile-name").value = category ? `${query} · ${category.label}` : `${query} · ${sourceLabel(source)}`;
  $("#profile-source").value = source;
  $("#profile-url").value = buildWizardSearchUrl(source, query, category, selectedTypes);
  setKleinanzeigenTypes("profile", selectedTypes);
  $("#profile-interval").value = 120;
  const wizardLocation = $("#wizard-location").value.trim();
  $("#profile-location-query").value = wizardLocation;
  $("#profile-location-radius").value = wizardLocation ? $("#wizard-location-radius").value : "";
  setLocationMode("text");
  $("#profile-min-price").value = "";
  $("#profile-max-price").value = $("#wizard-max-price").value;
  $("#profile-max-age").value = $("#wizard-max-age").value || 365;
  $("#profile-include").value = query.split(/\s+/).filter(Boolean).join("\n");
  $("#profile-required").value = $("#wizard-required").value;
  $("#profile-exclude").value = $("#wizard-exclude").value;
  $("#profile-categories").value = "";
  syncAllChipInputs();
  renderGuidedFilterRules();
  $("#profile-enabled").checked = $("#wizard-enabled").checked;
  $("#profile-notify").checked = $("#wizard-notify").checked;
  $("#profile-notify-webhook").checked = $("#wizard-notify-webhook").checked;
  updateSourcePlaceholder();
  updateKleinanzeigenTypeVisibility();
  updateFilterPreview();
  await saveProfile();
  clearWizard();
  $("#profile-wizard").classList.add("hidden");
  $("#profile-form").classList.remove("hidden");
}

function clearWizard() {
  $("#wizard-source").value = "kleinanzeigen";
  updateWizardCategories();
  setKleinanzeigenTypes("wizard", ["angebote", "gesuche"]);
  $("#wizard-query").value = "";
  $("#wizard-max-price").value = "";
  $("#wizard-max-age").value = 365;
  $("#wizard-location").value = "";
  $("#wizard-location-radius").value = "";
  $("#wizard-required").value = "";
  $("#wizard-exclude").value = "";
  syncAllChipInputs();
  $("#wizard-enabled").checked = false;
  $("#wizard-notify").checked = false;
  $("#wizard-notify-webhook").checked = false;
  setWizardStep(0);
  updateWizardSummary();
}

function updateWizardCategories() {
  const source = $("#wizard-source").value;
  const current = $("#wizard-category").value;
  const categories = providerCategories[source] || [];
  $("#wizard-category").innerHTML = `
    <option value="">${escapeHtml(t("wizard.allCategories"))}</option>
    ${categories.map((category) => `<option value="${escapeAttribute(category.id || category.slug)}">${escapeHtml(category.label)}</option>`).join("")}
  `;
  $("#wizard-category").value = categories.some((category) => (category.id || category.slug) === current) ? current : "";
  updateKleinanzeigenTypeVisibility();
  updateWizardSummary();
}

function selectedWizardCategory() {
  const source = $("#wizard-source").value;
  const value = $("#wizard-category").value;
  if (!value) return null;
  return (providerCategories[source] || []).find((category) => (category.id || category.slug) === value) || null;
}

async function createWizardDraftWithAi() {
  const prompt = $("#wizard-ai-prompt").value.trim();
  if (!prompt) return toast(t("toast.searchRequired"));
  const button = $("#wizard-ai-button");
  button.disabled = true;
  try {
    const draft = await api("/api/ai/search-draft", {
      method: "POST",
      body: JSON.stringify({ prompt, language: state.language }),
    });
    applyWizardDraft(draft);
    toast(t("toast.searchDraftCreated"));
  } catch (error) {
    toast(errorMessage(error));
  } finally {
    button.disabled = false;
  }
}

function applyWizardDraft(draft) {
  const source = ["kleinanzeigen", "facebook", "mobilede", "marktplaats"].includes(draft.source_type) ? draft.source_type : "kleinanzeigen";
  $("#wizard-source").value = source;
  updateWizardCategories();
  const category = matchWizardCategory(source, draft.category_hint || "");
  $("#wizard-category").value = category ? (category.id || category.slug) : "";
  updateKleinanzeigenTypeVisibility();
  $("#wizard-query").value = draft.query || "";
  $("#wizard-max-price").value = draft.max_price ?? "";
  $("#wizard-max-age").value = draft.max_listing_age_days || 365;
  $("#wizard-location").value = draft.location || "";
  $("#wizard-location-radius").value = draft.radius_km ? String(draft.radius_km) : "";
  $("#wizard-required").value = (draft.required_keywords || []).join("\n");
  $("#wizard-exclude").value = (draft.exclude_keywords || []).join("\n");
  syncAllChipInputs();
  setWizardStep(1);
  updateWizardSummary();
}

function matchWizardCategory(source, hint) {
  const normalized = normalizeCategoryHint(hint);
  if (!normalized) return null;
  return (providerCategories[source] || []).find((category) => {
    return [category.label, category.slug, category.id, category.path, ...(category.aliases || [])]
      .filter(Boolean)
      .some((value) => normalizeCategoryHint(value).includes(normalized) || normalized.includes(normalizeCategoryHint(value)));
  }) || null;
}

function normalizeCategoryHint(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function updateWizardSummary() {
  const target = $("#wizard-summary");
  if (!target) return;
  const query = $("#wizard-query").value.trim();
  if (!query) {
    target.innerHTML = `<strong>${escapeHtml(t("wizard.summaryTitle"))}</strong><p class="meta">${escapeHtml(t("wizard.summaryEmpty"))}</p>`;
    return;
  }
  const source = sourceLabel($("#wizard-source").value);
  const category = selectedWizardCategory()?.label || t("wizard.allCategories");
  const location = $("#wizard-location").value.trim();
  const radius = $("#wizard-location-radius").value;
  const price = $("#wizard-max-price").value;
  const maxAge = $("#wizard-max-age").value || 365;
  const required = listFromText($("#wizard-required").value);
  const excluded = listFromText($("#wizard-exclude").value);
  const automation = [
    $("#wizard-enabled").checked ? t("form.backgroundPolling") : "",
    $("#wizard-notify").checked ? t("form.telegram") : "",
    $("#wizard-notify-webhook").checked ? t("form.webhook") : "",
  ].filter(Boolean);
  const lines = [
    `${source} · ${category}`,
    price ? `${t("wizard.maxPrice")}: ${price} EUR` : "",
    maxAge ? `${t("profile.maxAgeShort")}: ${t("profile.maxAgeDays", { days: maxAge })}` : "",
    location ? `${t("wizard.location")}: ${location}${radius ? ` +${radius} km` : ""}` : "",
    required.length ? `${t("wizard.mustInclude")}: ${required.join(", ")}` : "",
    excluded.length ? `${t("wizard.hideWords")}: ${excluded.join(", ")}` : "",
    automation.length ? automation.join(" · ") : "",
  ].filter(Boolean);
  target.innerHTML = `
    <strong>${escapeHtml(t("wizard.summaryTitle"))}</strong>
    <h4>${escapeHtml(query)}</h4>
    ${lines.map((line) => `<p class="meta">${escapeHtml(line)}</p>`).join("")}
  `;
}

function buildWizardSearchUrl(source, query, category, kleinanzeigenTypes = selectedKleinanzeigenTypes("wizard")) {
  if (source === "facebook") {
    const base = category?.slug
      ? `https://www.facebook.com/marketplace/category/${category.slug}/`
      : "https://www.facebook.com/marketplace/search/";
    return `${base}?query=${encodeURIComponent(query)}`;
  }
  if (source === "mobilede") {
    const path = category?.path || "fahrzeuge/auto/search.html";
    return `https://suchen.mobile.de/${path}?ft=${encodeURIComponent(query)}`;
  }
  if (source === "marktplaats") {
    const path = category?.path ? `/l/${category.path}/q/` : "/q/";
    return `https://www.marktplaats.nl${path}${keywordUrlPath(query)}/`;
  }
  if (source === "kleinanzeigen" && category?.id && category?.path) {
    return `https://www.kleinanzeigen.de/s-${category.path}${kleinanzeigenTypeSegment(kleinanzeigenTypes)}/${keywordUrlPath(query)}/k0c${category.id}`;
  }
  if (source === "kleinanzeigen" && kleinanzeigenTypes.length === 1) {
    return `https://www.kleinanzeigen.de/s-anzeige:${kleinanzeigenTypes[0]}/${keywordUrlPath(query)}/k0`;
  }
  return `https://www.kleinanzeigen.de/s-suchanfrage.html?keywords=${encodeURIComponent(query)}`;
}

async function saveProfile() {
  const payload = profilePayload();
  const urlError = validateProfileUrl(payload);
  if (urlError) throw new Error(urlError);
  const id = $("#profile-id").value;
  const saved = await api(id ? `/api/profiles/${id}` : "/api/profiles", {
    method: id ? "PUT" : "POST",
    body: JSON.stringify(payload),
  });
  toast(t("toast.profileSaved"));
  editProfile(saved);
  await refreshAll();
}

function validateProfileUrl(payload) {
  if (payload.source_type !== "facebook") return "";
  try {
    const url = new URL(payload.search_url);
    const path = url.pathname.replace(/\/+$/, "").toLowerCase();
    if (path === "/marketplace/search" && !url.searchParams.get("query")?.trim()) {
      return t("toast.facebookSearchQueryRequired");
    }
  } catch {
    return "";
  }
  return "";
}

function errorMessage(error) {
  return String(error?.message || error).replace(/^\d+\s+/, "");
}

async function runSelectedProfile() {
  const id = $("#profile-id").value;
  if (!id) return toast(t("toast.saveProfileFirst"));
  toast(t("toast.runStarted"));
  const result = await api(`/api/profiles/${id}/run`, { method: "POST" });
  toast(t("toast.runComplete", result));
  await refreshAll();
}

async function runListingProfile() {
  const id = $("#listing-profile-filter").value;
  if (!id) return toast(t("toast.selectJobFirst"));
  const button = $("#run-listing-profile-button");
  button.disabled = true;
  toast(t("toast.runStarted"));
  try {
    const result = await api(`/api/profiles/${id}/run`, { method: "POST" });
    toast(t("toast.runComplete", result));
    state.listingPage = 0;
    await refreshAll();
  } catch (error) {
    toast(errorMessage(error));
  } finally {
    updateListingRunButton();
  }
}

function updateListingRunButton() {
  const button = $("#run-listing-profile-button");
  if (!button) return;
  const hasSelection = Boolean($("#listing-profile-filter").value);
  button.disabled = !hasSelection;
  button.title = hasSelection ? t("listings.runSelectedJob") : t("listings.runSelectedJobHint");
}

async function deleteSelectedProfile() {
  const id = $("#profile-id").value;
  if (!id) return;
  await api(`/api/profiles/${id}`, { method: "DELETE" });
  toast(t("toast.profileDeleted"));
  editProfile(null);
  await refreshAll();
}

function profilePayload() {
  syncLocationCriteria();
  return {
    name: $("#profile-name").value,
    enabled: $("#profile-enabled").checked,
    source_type: $("#profile-source").value,
    search_url: $("#profile-url").value,
    poll_interval_minutes: Number($("#profile-interval").value || 60),
    include_keywords: lines("#profile-include"),
    required_keywords: lines("#profile-required"),
    exclude_keywords: lines("#profile-exclude"),
    excluded_categories: lines("#profile-categories"),
    min_price: numberOrNull("#profile-min-price"),
    max_price: numberOrNull("#profile-max-price"),
    max_listing_age_days: Number($("#profile-max-age").value || 365),
    location_hint: $("#profile-location").value,
    notify_telegram: $("#profile-notify").checked,
    notify_webhook: $("#profile-notify-webhook").checked,
  };
}

function updateFilterPreview() {
  const chips = [];
  const location = $("#profile-location").value.trim();
  const minPrice = $("#profile-min-price").value;
  const maxPrice = $("#profile-max-price").value;
  if (location) chips.push(`${t("profile.locationHint")}: ${location}`);
  if (minPrice) chips.push(`${t("profile.minPriceShort")} ${minPrice} EUR`);
  if (maxPrice) chips.push(`${t("profile.maxPriceShort")} ${maxPrice} EUR`);
  chips.push(`${t("profile.maxAgeShort")}: ${t("profile.maxAgeDays", { days: $("#profile-max-age").value || 365 })}`);
  if ($("#profile-source").value === "kleinanzeigen") {
    chips.push(`${t("listingTypes.title")}: ${kleinanzeigenTypeLabel()}`);
  }
  lines("#profile-required").forEach((item) => chips.push(`${t("profile.required")}: ${item}`));
  lines("#profile-include").slice(0, 5).forEach((item) => chips.push(`match: ${item}`));
  lines("#profile-exclude").forEach((item) => chips.push(`${t("profile.exclude")}: ${item}`));
  lines("#profile-categories").forEach((item) => chips.push(`${t("profile.hiddenCategories")}: ${item}`));
  chips.push($("#profile-enabled").checked ? t("form.backgroundPolling") : "Polling off");
  chips.push($("#profile-notify").checked ? t("form.telegramNotifications") : "Telegram off");
  chips.push($("#profile-notify-webhook").checked ? t("form.webhookNotifications") : t("jobSummary.webhookOff"));
  $("#profile-filter-preview").innerHTML = chips.map((chip) => `<span>${escapeHtml(chip)}</span>`).join("");
  updateJobSetupSummary();
}

function updateSourcePlaceholder() {
  const source = $("#profile-source").value;
  $("#profile-url").placeholder = {
    kleinanzeigen: "https://www.kleinanzeigen.de/...",
    facebook: "https://www.facebook.com/marketplace/search/?query=defekt",
    mobilede: "https://suchen.mobile.de/fahrzeuge/auto/search.html?ft=tesla",
    html: "https://example.com/search-results",
  }[source] || "https://example.com/search-results";
  updateSourceOptions();
  updateKleinanzeigenTypeVisibility();
  renderUrlParameterPreview();
  updateJobSetupSummary();
}

function selectSource(source) {
  $("#profile-source").value = source;
  const current = $("#profile-url").value.trim();
  if (!current || Object.values(sourceBaseUrls()).includes(current)) {
    $("#profile-url").value = sourceBaseUrl(source);
  }
  updateSourcePlaceholder();
  syncProfileParametersFromUrl(false);
}

function updateSourceOptions() {
  const source = $("#profile-source").value;
  $$("[data-source-option]").forEach((button) => {
    button.classList.toggle("active", button.dataset.sourceOption === source);
  });
}

function openSelectedSource() {
  const baseUrl = sourceBaseUrl($("#profile-source").value);
  if (baseUrl) window.open(baseUrl, "_blank", "noopener");
  else $("#profile-url").focus();
}

function updateJobSetupSummary() {
  const name = $("#profile-name").value.trim() || t("jobSummary.nameMissing");
  const url = $("#profile-url").value.trim() || t("jobSummary.urlMissing");
  const interval = Number($("#profile-interval").value || 60);
  const chips = [
    `${t("profile.name")}: ${name}`,
    `${t("jobSummary.provider")}: ${sourceLabel($("#profile-source").value)}`,
    $("#profile-source").value === "kleinanzeigen" ? `${t("listingTypes.title")}: ${kleinanzeigenTypeLabel()}` : "",
    url,
    t("jobSummary.interval", { minutes: interval }),
    $("#profile-enabled").checked ? t("jobSummary.pollingOn") : t("jobSummary.pollingOff"),
    $("#profile-notify").checked ? t("jobSummary.telegramOn") : t("jobSummary.telegramOff"),
    $("#profile-notify-webhook").checked ? t("jobSummary.webhookOn") : t("jobSummary.webhookOff"),
  ];
  $("#job-setup-summary").innerHTML = chips.filter(Boolean).map((chip) => `<span>${escapeHtml(chip)}</span>`).join("");
}

async function loadListings() {
  await loadListingBrowser("#listings-table", false);
}

async function loadWatchlist() {
  await loadListingBrowser("#watchlist-table", true);
}

async function loadReviewQueue() {
  const query = new URLSearchParams({
    status: "new",
    include_hidden: "false",
    sort: "date_desc",
    limit: "50",
    offset: "0",
    paged: "true",
  });
  const result = await api(`/api/listings?${query}`);
  state.reviewQueue = result.items || [];
  state.reviewIndex = Math.min(state.reviewIndex, Math.max(0, state.reviewQueue.length - 1));
  renderReviewCard();
}

function currentReviewListing() {
  return state.reviewQueue[state.reviewIndex] || null;
}

function renderReviewCard() {
  const target = $("#review-card");
  if (!target) return;
  const listing = currentReviewListing();
  const watchButton = $("#review-watch-button");
  const watchMenuButton = $("#review-watch-menu-button");
  const seenButton = $("#review-seen-button");
  const inquiryButton = $("#review-inquiry-button");
  const openButton = $("#review-open-button");
  [watchButton, watchMenuButton, seenButton, inquiryButton, openButton].forEach((button) => {
    if (button) button.disabled = !listing;
  });
  if (inquiryButton) inquiryButton.classList.toggle("hidden", !state.aiEnabled);
  renderReviewWatchMenu(listing);
  if (!listing) {
    target.innerHTML = `
      <article class="review-card empty-review">
        <strong>${escapeHtml(t("review.empty"))}</strong>
        <p class="meta">${escapeHtml(t("review.emptyHint"))}</p>
      </article>
    `;
    return;
  }
  target.innerHTML = reviewListingMarkup(listing);
  const card = target.querySelector("[data-review-card]");
  bindReviewGestures(card);
  target.querySelector("[data-review-watch]")?.addEventListener("click", reviewWatchCurrent);
  target.querySelector("[data-review-contacted]")?.addEventListener("click", reviewContactedCurrent);
  target.querySelector("[data-review-seen]")?.addEventListener("click", reviewSeenCurrent);
  target.querySelector("[data-review-open]")?.addEventListener("click", reviewOpenCurrent);
  target.querySelector("[data-review-inquiry]")?.addEventListener("click", reviewInquiryCurrent);
  target.querySelector("[data-review-assessment]")?.addEventListener("click", (event) => reviewAssessmentCurrent(event.currentTarget));
  target.querySelector("[data-map-location]")?.addEventListener("click", (event) => {
    openListingMap(event.currentTarget.dataset.mapLocation, event.currentTarget.dataset.mapTitle);
  });
}

function reviewListingMarkup(listing) {
  const watchlistBadges = listing.watchlists?.length
    ? listing.watchlists.map((watchlist) => `<span class="pill watchlist-pill">${escapeHtml(watchlist.name)}</span>`).join("")
    : (listing.watchlisted ? `<span class="pill watchlist-pill">${escapeHtml(t("summary.watchlist"))}</span>` : "");
  const detailFacts = [
    listingDateFact(listing),
    ...locationFacts(listing),
    ...(listing.category_text ? [listing.category_text] : []),
  ].filter(Boolean);
  return `
    <article class="review-card" data-review-card data-id="${listing.id}">
      <div class="review-image-wrap">
        ${listing.thumbnail_url ? `<img class="review-image" src="/api/listings/${listing.id}/image" alt="">` : `<div class="review-image placeholder">${escapeHtml(t("listing.noImage"))}</div>`}
      </div>
      <div class="review-details">
        <div class="review-provider-row">
          <span class="source-badge ${escapeAttribute(listing.source_type)}">${escapeHtml(sourceLabel(listing.source_type))}</span>
          <span class="pill availability ${escapeAttribute(listing.availability_status || "unknown")}">${escapeHtml(availabilityLabel(listing.availability_status))}</span>
          ${listing.contacted ? `<span class="pill contacted">${escapeHtml(t("listing.contacted"))}</span>` : ""}
          ${watchlistBadges}
        </div>
        <h3>${escapeHtml(listing.title)}</h3>
        ${listing.description_snippet ? `<p class="review-description">${escapeHtml(listing.description_snippet)}</p>` : ""}
        <strong class="review-price">${escapeHtml(listing.price_text || t("listing.noPrice"))}</strong>
        <div class="listing-facts">
          ${factsMarkup(detailFacts, listing)}
        </div>
        <p class="review-reason">${escapeHtml(t("review.reason", { score: listing.score }))}</p>
        ${listing.ai_assessment_text ? `
          <div class="ai-assessment">
            <strong>${escapeHtml(t("listing.aiAssessment"))}</strong>
            <p>${escapeHtml(listing.ai_assessment_text)}</p>
          </div>
        ` : ""}
        <div class="review-card-actions">
          <button class="button ghost" type="button" data-review-watch>${escapeHtml(t("review.watch"))}</button>
          <button class="button ghost" type="button" data-review-contacted>${escapeHtml(t(listing.contacted ? "listing.unmarkContacted" : "listing.markContacted"))}</button>
          <button class="button primary" type="button" data-review-open>${escapeHtml(t("review.open"))}</button>
          <button class="button ghost" type="button" data-review-seen>${escapeHtml(t("review.seen"))}</button>
          ${state.aiEnabled ? `<button class="button ghost" type="button" data-review-inquiry>${escapeHtml(t("listing.aiInquiry"))}</button>` : ""}
          ${state.aiEnabled && state.aiAssessmentsEnabled ? `<button class="button ghost" type="button" data-review-assessment>${escapeHtml(t("listing.aiAssessment"))}</button>` : ""}
        </div>
      </div>
    </article>
  `;
}

function bindReviewGestures(card) {
  if (!card) return;
  card.addEventListener("dblclick", reviewWatchCurrent);
  card.addEventListener("pointerdown", (event) => {
    state.reviewPointer = { x: event.clientX, y: event.clientY, id: event.pointerId };
    card.setPointerCapture?.(event.pointerId);
  });
  card.addEventListener("pointerup", async (event) => {
    const start = state.reviewPointer;
    state.reviewPointer = null;
    if (!start || start.id !== event.pointerId) return;
    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    if (Math.abs(dx) > 90 && Math.abs(dx) > Math.abs(dy) * 1.4) {
      await reviewSeenCurrent();
    }
  });
}

async function reviewWatchCurrent() {
  const listing = currentReviewListing();
  if (!listing) return;
  const watchlist = defaultWatchlist();
  await addListingToWatchlist(listing.id, watchlist?.id);
  listing.watchlisted = true;
  if (watchlist && !listing.watchlists?.some((item) => item.id === watchlist.id)) {
    listing.watchlists = [...(listing.watchlists || []), { id: watchlist.id, name: watchlist.name }];
  }
  toast(watchlist ? t("toast.watchlistAddedTo", { name: watchlist.name }) : t("toast.watchlistAdded"));
  renderReviewCard();
  await Promise.all([loadWatchlist(), loadWatchlistsMeta(), loadSummary()]);
}

async function reviewSeenCurrent() {
  const listing = currentReviewListing();
  if (!listing) return;
  await api(`/api/listings/${listing.id}`, {
    method: "PATCH",
    body: JSON.stringify({ status: "seen" }),
  });
  toast(t("toast.listingSeen"));
  state.reviewQueue.splice(state.reviewIndex, 1);
  if (state.reviewIndex >= state.reviewQueue.length) state.reviewIndex = Math.max(0, state.reviewQueue.length - 1);
  renderReviewCard();
  await Promise.all([loadListings(), loadSummary()]);
}

async function reviewContactedCurrent() {
  const listing = currentReviewListing();
  if (!listing) return;
  const contacted = !listing.contacted;
  const updated = await api(`/api/listings/${listing.id}`, {
    method: "PATCH",
    body: JSON.stringify({ contacted }),
  });
  Object.assign(listing, updated);
  toast(t("toast.contactedChanged"));
  renderReviewCard();
  await Promise.all([loadListings(), loadWatchlist(), loadSummary()]);
}

function reviewOpenCurrent() {
  const listing = currentReviewListing();
  if (listing?.listing_url) window.open(listing.listing_url, "_blank", "noopener");
}

function reviewInquiryCurrent() {
  const listing = currentReviewListing();
  if (!listing) return;
  generateInquiry(listing.id, $("#review-inquiry-button"));
}

function reviewAssessmentCurrent(button) {
  const listing = currentReviewListing();
  if (!listing) return;
  generateAssessment(listing.id, button);
}

async function generateInquiry(listingId, button) {
  if (!listingId) return;
  if (button) button.disabled = true;
  try {
    const result = await api(`/api/listings/${listingId}/inquiry`, {
      method: "POST",
      body: JSON.stringify({ language: state.language }),
    });
    $("#inquiry-text").value = result.text || "";
    $("#inquiry-dialog").showModal();
    toast(t("toast.inquiryGenerated"));
  } catch (error) {
    toast(errorMessage(error));
  } finally {
    if (button) button.disabled = false;
  }
}

async function openListingMap(location, title) {
  const query = String(location || "").trim();
  if (!query) return toast(t("listing.locationMapUnavailable"));
  const dialog = $("#listing-map-dialog");
  const status = $("#listing-map-status");
  const frame = $("#listing-map-frame");
  const openLink = $("#listing-map-open");
  $("#listing-map-title").textContent = t("listing.locationMapTitle");
  $("#listing-map-subtitle").textContent = `${title || ""}${title ? " · " : ""}${query}`;
  status.textContent = t("listing.locationMapLoading");
  status.classList.remove("hidden");
  frame.classList.add("hidden");
  frame.removeAttribute("src");
  openLink.classList.add("hidden");
  openLink.removeAttribute("href");
  dialog.showModal();
  try {
    const result = await geocodeListingLocation(query);
    if (!result) throw new Error("location unavailable");
    frame.src = osmEmbedUrl(result.lat, result.lng);
    frame.classList.remove("hidden");
    openLink.href = osmSearchUrl(query);
    openLink.classList.remove("hidden");
    status.classList.add("hidden");
  } catch {
    status.textContent = t("listing.locationMapUnavailable");
    openLink.href = osmSearchUrl(query);
    openLink.classList.remove("hidden");
  }
}

async function geocodeListingLocation(query) {
  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.searchParams.set("format", "jsonv2");
  url.searchParams.set("limit", "1");
  url.searchParams.set("countrycodes", "de");
  url.searchParams.set("q", query);
  const response = await fetch(url.toString(), { headers: { "Accept": "application/json" } });
  if (!response.ok) return null;
  const results = await response.json();
  const first = Array.isArray(results) ? results[0] : null;
  if (!first?.lat || !first?.lon) return null;
  return { lat: Number(first.lat), lng: Number(first.lon) };
}

function osmEmbedUrl(lat, lng) {
  const latitude = Number(lat);
  const longitude = Number(lng);
  const latPad = 0.015;
  const lngPad = 0.025;
  const url = new URL("https://www.openstreetmap.org/export/embed.html");
  url.searchParams.set("bbox", `${longitude - lngPad},${latitude - latPad},${longitude + lngPad},${latitude + latPad}`);
  url.searchParams.set("layer", "mapnik");
  url.searchParams.set("marker", `${latitude},${longitude}`);
  return url.toString();
}

function osmSearchUrl(query) {
  const url = new URL("https://www.openstreetmap.org/search");
  url.searchParams.set("query", query);
  return url.toString();
}

async function generateAssessment(listingId, button, options = {}) {
  if (!listingId) return;
  const silent = Boolean(options.silent);
  const refresh = options.refresh !== false;
  if (button) button.disabled = true;
  try {
    const result = await api(`/api/listings/${listingId}/assessment`, { method: "POST" });
    const applyAssessment = (listing) => {
      if (!listing || Number(listing.id) !== Number(listingId)) return listing;
      return {
        ...listing,
        ai_assessment_text: result.text || "",
        ai_assessed_at: result.assessed_at || null,
      };
    };
    state.reviewQueue = state.reviewQueue.map(applyAssessment);
    if (!silent) toast(t("toast.assessmentGenerated"));
    renderReviewCard();
    if (refresh) await Promise.all([loadListings(), loadWatchlist()]);
  } catch (error) {
    if (silent) console.warn("Automatic AI assessment failed", error);
    else toast(errorMessage(error));
  } finally {
    if (button) button.disabled = false;
  }
}

async function copyInquiryText() {
  const text = $("#inquiry-text").value;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    toast(t("toast.inquiryCopied"));
  } catch {
    $("#inquiry-text").focus();
    $("#inquiry-text").select();
  }
}

function renderReviewWatchMenu(listing) {
  const menu = $("#review-watch-menu");
  if (!menu) return;
  menu.classList.add("hidden");
  menu.innerHTML = listing ? watchlistMenuMarkup(listing.id) : "";
}

function toggleReviewWatchMenu(event) {
  event.stopPropagation();
  const menu = $("#review-watch-menu");
  if (!menu) return;
  menu.classList.toggle("hidden");
  bindWatchlistMenu(menu);
}

function defaultWatchlist() {
  return state.watchlists.find((watchlist) => watchlist.id === Number(state.defaultWatchlistId)) || state.watchlists[0] || null;
}

async function addListingToWatchlist(listingId, watchlistId) {
  await api(`/api/listings/${listingId}`, {
    method: "PATCH",
    body: JSON.stringify({ watchlisted: true, watchlist_id: watchlistId || null }),
  });
}

async function removeListingFromWatchlists(listingId) {
  await api(`/api/listings/${listingId}`, {
    method: "PATCH",
    body: JSON.stringify({ watchlisted: false }),
  });
}

function watchlistMenuMarkup(listingId) {
  const listItems = state.watchlists.map((watchlist) => `
    <button type="button" data-watchlist-select="${watchlist.id}" data-id="${listingId}">
      ${escapeHtml(t("listing.addToWatchlist", { name: watchlist.name }))}
    </button>
  `).join("");
  return `
    ${listItems}
    <button type="button" data-watchlist-create data-id="${listingId}">${escapeHtml(t("settings.createWatchlist"))}</button>
  `;
}

function bindWatchlistMenu(root) {
  if (root.dataset.bound === "true") return;
  root.dataset.bound = "true";
  root.addEventListener("click", async (event) => {
    event.stopPropagation();
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.watchlistSelect) {
      button.disabled = true;
      const watchlist = state.watchlists.find((item) => item.id === Number(button.dataset.watchlistSelect));
      await addListingToWatchlist(button.dataset.id, watchlist?.id);
      toast(watchlist ? t("toast.watchlistAddedTo", { name: watchlist.name }) : t("toast.watchlistAdded"));
      await Promise.all([loadListings(), loadWatchlist(), loadReviewQueue(), loadWatchlistsMeta(), loadSummary()]);
      return;
    }
    if (button.hasAttribute("data-watchlist-create")) {
      const name = window.prompt(t("listing.newWatchlistPrompt"));
      if (!name?.trim()) return;
      button.disabled = true;
      const watchlist = await api("/api/watchlists", {
        method: "POST",
        body: JSON.stringify({ name: name.trim() }),
      });
      await addListingToWatchlist(button.dataset.id, watchlist.id);
      state.defaultWatchlistId = watchlist.id;
      await Promise.all([loadWatchlistsMeta(), saveSettings(), loadListings(), loadWatchlist(), loadReviewQueue(), loadSummary()]);
      toast(t("toast.watchlistAddedTo", { name: watchlist.name }));
    }
  });
}

async function loadListingBrowser(containerSelector, watchlistedOnly) {
  const browser = $(containerSelector);
  if (!browser) return;
  if (!state.watchlists.length) await loadWatchlistsMeta();
  const page = watchlistedOnly ? state.watchlistPage : state.listingPage;
  const pageSize = state.pageSize;
  const status = $("#listing-status-filter").value;
  const profileId = $("#listing-profile-filter").value;
  const search = $("#listing-search-filter").value;
  const minPrice = $("#listing-min-price-filter").value;
  const maxPrice = $("#listing-max-price-filter").value;
  const includeHidden = $("#include-hidden").checked;
  const query = new URLSearchParams();
  if (!watchlistedOnly) {
    if (status) query.set("status", status);
    if (profileId) query.set("profile_id", profileId);
    if (search) query.set("q", search);
    if (minPrice) query.set("min_price", minPrice);
    if (maxPrice) query.set("max_price", maxPrice);
    query.set("include_hidden", String(includeHidden));
  }
  if (watchlistedOnly) query.set("watchlisted", "true");
  query.set("sort", $("#listing-sort-filter").value);
  query.set("limit", String(pageSize));
  query.set("offset", String(page * pageSize));
  query.set("paged", "true");
  const result = await api(`/api/listings?${query}`);
  const listings = result.items || [];
  const total = result.total || 0;
  const maxPage = Math.max(0, Math.ceil(total / pageSize) - 1);
  if (page > maxPage) {
    if (watchlistedOnly) state.watchlistPage = maxPage;
    else state.listingPage = maxPage;
    return loadListingBrowser(containerSelector, watchlistedOnly);
  }
  browser.classList.toggle("grid-view", state.listingView === "grid");
  browser.classList.toggle("list-view", state.listingView !== "grid");
  updateListingViewButtons();
  updatePaginationControls(watchlistedOnly, total);
  if (!watchlistedOnly) updateListingsSummary(total);
  browser.innerHTML = listings.length
    ? listings.map((listing) => listingMarkup(listing)).join("")
    : `<article class="listing-card empty-listing"><strong>${escapeHtml(t(watchlistedOnly ? "empty.noWatchlist" : "empty.noListings"))}</strong><p class="meta">${escapeHtml(t(watchlistedOnly ? "empty.noWatchlistHint" : "empty.noListingsHint"))}</p></article>`;
  browser.querySelectorAll("[data-listing-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      await api(`/api/listings/${button.dataset.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: button.dataset.listingAction }),
      });
      toast(listingActionToast(button.dataset.listingAction));
      await Promise.all([loadListings(), loadWatchlist(), loadReviewQueue(), loadSummary()]);
    });
  });
  browser.querySelectorAll("[data-contacted-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      await api(`/api/listings/${button.dataset.id}`, {
        method: "PATCH",
        body: JSON.stringify({ contacted: button.dataset.contactedAction === "true" }),
      });
      toast(t("toast.contactedChanged"));
      await Promise.all([loadListings(), loadWatchlist(), loadReviewQueue(), loadSummary()]);
    });
  });
  browser.querySelectorAll("[data-watchlist-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      const added = button.dataset.watchlistAction === "add";
      if (added) {
        const watchlist = defaultWatchlist();
        await addListingToWatchlist(button.dataset.id, watchlist?.id);
        toast(watchlist ? t("toast.watchlistAddedTo", { name: watchlist.name }) : t("toast.watchlistAdded"));
      } else {
        await removeListingFromWatchlists(button.dataset.id);
        toast(t("toast.watchlistRemoved"));
      }
      await Promise.all([loadListings(), loadWatchlist(), loadReviewQueue(), loadWatchlistsMeta(), loadSummary()]);
    });
  });
  browser.querySelectorAll("[data-watchlist-menu-toggle]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const menu = button.closest(".watch-split")?.querySelector(".watch-menu");
      if (!menu) return;
      $$(".watch-menu").forEach((item) => {
        if (item !== menu) item.classList.add("hidden");
      });
      menu.classList.toggle("hidden");
      bindWatchlistMenu(menu);
    });
  });
  browser.querySelectorAll("[data-inquiry-action]").forEach((button) => {
    button.addEventListener("click", () => generateInquiry(button.dataset.id, button));
  });
  browser.querySelectorAll("[data-assessment-action]").forEach((button) => {
    button.addEventListener("click", () => generateAssessment(button.dataset.id, button));
  });
  browser.querySelectorAll("[data-map-location]").forEach((button) => {
    button.addEventListener("click", () => openListingMap(button.dataset.mapLocation, button.dataset.mapTitle));
  });
  browser.querySelectorAll(".listing-image").forEach((img) => {
    img.addEventListener("error", () => {
      const fallback = document.createElement("span");
      fallback.className = "no-image";
      fallback.textContent = t("listing.noImage");
      img.replaceWith(fallback);
    });
  });
  queueAutoAssessments(listings, containerSelector, watchlistedOnly, page);
}

function updateListingsSummary(total) {
  const summary = $("#listings-current-summary");
  if (!summary) return;
  summary.textContent = t("listings.resultSummary", { total });
}

function queueAutoAssessments(listings, containerSelector, watchlistedOnly, page) {
  if (!state.aiEnabled || !state.aiAssessmentsEnabled || !state.aiAssessmentsAutoEnabled) return;
  if ((watchlistedOnly && state.currentView !== "watchlist") || (!watchlistedOnly && state.currentView !== "listings")) return;
  if (state.autoAssessmentRunning || !Array.isArray(listings) || !listings.length) return;
  const batchKey = `${containerSelector}:${watchlistedOnly}:${page}:${listings.map((listing) => listing.id).join(",")}`;
  if (state.autoAssessmentBatches.has(batchKey)) return;
  const candidates = listings
    .filter((listing) => listing?.id && !listing.ai_assessment_text)
    .slice(0, AUTO_ASSESSMENT_BATCH_LIMIT);
  if (!candidates.length) return;
  state.autoAssessmentBatches.add(batchKey);
  state.autoAssessmentRunning = true;
  void (async () => {
    try {
      for (const listing of candidates) {
        await generateAssessment(listing.id, null, { silent: true, refresh: false });
      }
      if ((watchlistedOnly && state.currentView === "watchlist") || (!watchlistedOnly && state.currentView === "listings")) {
        await loadListingBrowser(containerSelector, watchlistedOnly);
      }
    } finally {
      state.autoAssessmentRunning = false;
    }
  })();
}

function resetListingsPage() {
  state.listingPage = 0;
  loadListings();
}

function setPageSize(value) {
  state.pageSize = [5, 10, 20, 50, 100].includes(Number(value)) ? Number(value) : 100;
  localStorage.setItem("marketplacelens.pageSize", String(state.pageSize));
  state.listingPage = 0;
  state.watchlistPage = 0;
  syncPageSizeControls();
  loadListings();
  loadWatchlist();
}

function syncPageSizeControls() {
  $$("[data-page-size]").forEach((select) => {
    select.value = String(state.pageSize);
  });
}

function changePage(watchlistedOnly, direction) {
  if (watchlistedOnly) {
    state.watchlistPage = Math.max(0, state.watchlistPage + direction);
    loadWatchlist();
  } else {
    state.listingPage = Math.max(0, state.listingPage + direction);
    loadListings();
  }
}

function updatePaginationControls(watchlistedOnly, total) {
  const control = $(watchlistedOnly ? "#watchlist-pagination" : "#listings-pagination");
  if (!control) return;
  const page = watchlistedOnly ? state.watchlistPage : state.listingPage;
  const start = total ? page * state.pageSize + 1 : 0;
  const end = Math.min(total, (page + 1) * state.pageSize);
  const maxPage = Math.max(0, Math.ceil(total / state.pageSize) - 1);
  control.querySelector("[data-page-info]").textContent = t("pagination.range", { start, end, total });
  control.querySelector("[data-page-prev]").disabled = page <= 0;
  control.querySelector("[data-page-next]").disabled = page >= maxPage;
}

function setListingView(view) {
  state.listingView = view === "grid" ? "grid" : "list";
  localStorage.setItem("marketplacelens.listingView", state.listingView);
  loadListings();
  loadWatchlist();
}

function updateListingViewButtons() {
  $$("[data-listing-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.listingView === state.listingView);
  });
}

function sortListings(listings) {
  const sort = $("#listing-sort-filter").value;
  const copy = [...listings];
  const price = (listing) => typeof listing.price_value === "number" ? listing.price_value : null;
  const comparePrice = (a, b, direction) => {
    const priceA = price(a);
    const priceB = price(b);
    if (priceA === null && priceB === null) return 0;
    if (priceA === null) return 1;
    if (priceB === null) return -1;
    return direction === "desc" ? priceB - priceA : priceA - priceB;
  };
  const seenAt = (listing) => new Date(listing.first_seen_at || 0).getTime();
  return copy.sort((a, b) => {
    if (sort === "price_asc") return comparePrice(a, b, "asc");
    if (sort === "price_desc") return comparePrice(a, b, "desc");
    if (sort === "score_desc") return (b.score || 0) - (a.score || 0);
    return seenAt(b) - seenAt(a);
  });
}

function locationFacts(listing) {
  const location = String(listing.location_text || "").trim();
  if (!location) return [`${t("listing.place")}: ${t("listing.noLocation")}`];
  const zipMatch = location.match(/\b\d{5}\b/);
  if (!zipMatch) return [`${t("listing.place")}: ${location}`];
  const zip = zipMatch[0];
  const place = location
    .replace(zip, "")
    .replace(/\s+/g, " ")
    .replace(/^[,\-·\s]+|[,\-·\s]+$/g, "")
    .trim();
  return [
    `${t("listing.postcode")}: ${zip}`,
    place ? `${t("listing.place")}: ${place}` : "",
  ].filter(Boolean);
}

function listingLocationQuery(listing) {
  return String(listing?.location_text || "").replace(/\s+/g, " ").trim();
}

function factsMarkup(facts, listing) {
  const factItems = facts.map((fact) => `<span>${escapeHtml(fact)}</span>`).join("");
  const location = listingLocationQuery(listing);
  if (!location) return factItems;
  return `${factItems}<button class="location-map-button" type="button" data-map-location="${escapeAttribute(location)}" data-map-title="${escapeAttribute(listing.title || location)}">${escapeHtml(t("listing.map"))}</button>`;
}

function listingDateFact(listing) {
  const posted = String(listing.posted_at_text || "").trim();
  if (posted) return `${t("listing.postedAt")}: ${posted}`;
  return "";
}

function listingMarkup(listing) {
  const watchlistAction = listing.watchlisted ? "remove" : "add";
  const watchlistLabel = listing.watchlisted ? t("listing.removeWatchlist") : t("listing.addWatchlist");
  const watchlistBadges = listing.watchlists?.length
    ? listing.watchlists.map((watchlist) => `<span class="pill watchlist-pill">★ ${escapeHtml(watchlist.name)}</span>`).join("")
    : (listing.watchlisted ? `<span class="pill watchlist-pill">★ ${escapeHtml(t("nav.watchlist"))}</span>` : "");
  const detailFacts = [
    ...(listing.profile_name ? [listing.profile_name] : []),
    listingDateFact(listing),
    ...locationFacts(listing),
    t("listing.score", { score: listing.score }),
  ].filter(Boolean);
  return `
    <article class="listing-card ${listing.watchlisted ? "watchlisted" : ""}">
      <div class="listing-media">
        ${listing.thumbnail_url ? `
          <img class="listing-image" src="/api/listings/${listing.id}/image" alt="${escapeAttribute(listing.title)}" loading="lazy">
        ` : `<span class="no-image">${escapeHtml(t("listing.noImage"))}</span>`}
      </div>
      <div class="listing-main">
        <div class="listing-title-row">
          <a href="${escapeAttribute(listing.listing_url)}" target="_blank" rel="noopener">${escapeHtml(listing.title)}</a>
          <div class="listing-badges">
            ${watchlistBadges}
            <span class="pill ${escapeAttribute(listing.status)}">${escapeHtml(statusLabel(listing.status))}</span>
            <span class="pill availability ${escapeAttribute(listing.availability_status || "unknown")}">${escapeHtml(availabilityLabel(listing.availability_status))}</span>
            ${listing.contacted ? `<span class="pill contacted">${escapeHtml(t("listing.contacted"))}</span>` : ""}
          </div>
        </div>
        <strong class="listing-price">${escapeHtml(listing.price_text || t("listing.noPrice"))}</strong>
        <p class="meta listing-description">${escapeHtml(listing.description_snippet || "")}</p>
        <div class="listing-facts">
          ${factsMarkup(detailFacts, listing)}
        </div>
        ${listing.filter_reason ? `<p class="filter-reason">${escapeHtml(listing.filter_reason)}</p>` : ""}
        ${listing.ai_assessment_text ? `
          <div class="ai-assessment compact">
            <strong>${escapeHtml(t("listing.aiAssessment"))}</strong>
            <p>${escapeHtml(listing.ai_assessment_text)}</p>
          </div>
        ` : ""}
      </div>
      <div class="row-actions">
        <div class="watch-split">
          <button class="mini-button watch-button ${listing.watchlisted ? "active" : ""}" data-watchlist-action="${watchlistAction}" data-id="${listing.id}">${listing.watchlisted ? "★" : "☆"} ${escapeHtml(watchlistLabel)}</button>
          <button class="mini-button watch-menu-toggle" type="button" data-watchlist-menu-toggle data-id="${listing.id}" aria-label="${escapeAttribute(t("listing.watchMenu"))}"></button>
          <div class="watch-menu hidden">${watchlistMenuMarkup(listing.id)}</div>
        </div>
        <button class="mini-button" data-listing-action="seen" data-id="${listing.id}">${escapeHtml(t("listing.seen"))}</button>
        <button class="mini-button contacted-toggle ${listing.contacted ? "active" : ""}" data-contacted-action="${listing.contacted ? "false" : "true"}" data-id="${listing.id}">${escapeHtml(t(listing.contacted ? "listing.unmarkContacted" : "listing.markContacted"))}</button>
        <button class="mini-button" data-listing-action="hidden" data-id="${listing.id}">${escapeHtml(t("listing.hide"))}</button>
        <button class="mini-button" data-listing-action="new" data-id="${listing.id}">${escapeHtml(t("listing.new"))}</button>
        ${state.aiEnabled ? `<button class="mini-button ai-button" data-inquiry-action data-id="${listing.id}">${escapeHtml(t("listing.aiInquiry"))}</button>` : ""}
        ${state.aiEnabled && state.aiAssessmentsEnabled ? `<button class="mini-button ai-button" data-assessment-action data-id="${listing.id}">${escapeHtml(t("listing.aiAssessment"))}</button>` : ""}
      </div>
    </article>
  `;
}

function statusLabel(status) {
  return t(`status.${status}`) || status;
}

function availabilityLabel(status) {
  return t(`availability.${status || "unknown"}`) || status || t("availability.unknown");
}

function listingActionToast(action) {
  if (action === "hidden") return t("toast.listingHidden");
  if (action === "seen") return t("toast.listingSeen");
  if (action === "new") return t("toast.listingNew");
  return statusLabel(action);
}

async function loadSettings() {
  await loadWatchlistsMeta();
  const settings = await api("/api/settings");
  state.defaultWatchlistId = settings.default_watchlist_id;
  $("#telegram-token").value = settings.telegram_bot_token;
  $("#telegram-chat").value = settings.telegram_chat_id;
  $("#webhook-url").value = settings.webhook_url;
  $("#global-rate").value = settings.global_rate_limit_seconds;
  state.aiEnabled = Boolean(settings.ai_enabled);
  state.aiAssessmentsEnabled = Boolean(settings.ai_listing_assessments_enabled);
  state.aiAssessmentsAutoEnabled = Boolean(settings.ai_listing_assessments_auto_enabled);
  state.aiAssessmentsNewEnabled = Boolean(settings.ai_listing_assessments_new_enabled);
  $("#ai-enabled").checked = Boolean(settings.ai_enabled);
  $("#ai-assessments-enabled").checked = Boolean(settings.ai_listing_assessments_enabled);
  $("#ai-assessments-auto-enabled").checked = Boolean(settings.ai_listing_assessments_auto_enabled);
  $("#ai-assessments-new-enabled").checked = Boolean(settings.ai_listing_assessments_new_enabled);
  $("#ai-provider").value = settings.ai_provider || "openai";
  $("#ai-api-key").value = settings.ai_api_key || "";
  $("#ai-base-url").value = settings.ai_base_url || "";
  $("#ai-model").value = settings.ai_model || "";
  $("#ai-tone").value = settings.ai_tone || "normal";
  $("#facebook-cookie-header").value = settings.facebook_cookie_header || "";
  updateAiProviderHints();
  renderDefaultWatchlistSelect();
}

async function loadAccountProfile() {
  const profile = await api("/api/account");
  state.accountProfile = profile;
  $("#account-display-name").value = profile.display_name || "";
  $("#account-buyer-location").value = profile.buyer_location || "";
  $("#account-contact-hint").value = profile.contact_hint || "";
  $("#account-inquiry-signature").value = profile.inquiry_signature || "";
}

async function saveAccountProfile() {
  const profile = await api("/api/account", {
    method: "PUT",
    body: JSON.stringify({
      display_name: $("#account-display-name").value,
      buyer_location: $("#account-buyer-location").value,
      contact_hint: $("#account-contact-hint").value,
      inquiry_signature: $("#account-inquiry-signature").value,
    }),
  });
  state.accountProfile = profile;
  toast(t("toast.profileSaved"));
}

async function saveSettings() {
  const settings = await api("/api/settings", {
    method: "PUT",
    body: JSON.stringify({
      telegram_bot_token: $("#telegram-token").value,
      telegram_chat_id: $("#telegram-chat").value,
      webhook_url: $("#webhook-url").value,
      global_rate_limit_seconds: Number($("#global-rate").value || 20),
      default_watchlist_id: Number($("#default-watchlist").value || state.defaultWatchlistId || 0),
      ai_enabled: $("#ai-enabled").checked,
      ai_listing_assessments_enabled: $("#ai-assessments-enabled").checked,
      ai_listing_assessments_auto_enabled: $("#ai-assessments-auto-enabled").checked,
      ai_listing_assessments_new_enabled: $("#ai-assessments-new-enabled").checked,
      ai_provider: $("#ai-provider").value,
      ai_api_key: $("#ai-api-key").value,
      ai_base_url: $("#ai-base-url").value,
      ai_model: $("#ai-model").value,
      ai_tone: $("#ai-tone").value,
      facebook_cookie_header: $("#facebook-cookie-header").value,
    }),
  });
  state.defaultWatchlistId = settings.default_watchlist_id;
  state.aiEnabled = Boolean(settings.ai_enabled);
  state.aiAssessmentsEnabled = Boolean(settings.ai_listing_assessments_enabled);
  state.aiAssessmentsAutoEnabled = Boolean(settings.ai_listing_assessments_auto_enabled);
  state.aiAssessmentsNewEnabled = Boolean(settings.ai_listing_assessments_new_enabled);
  state.autoAssessmentBatches.clear();
  renderDefaultWatchlistSelect();
  toast(t("toast.settingsSaved"));
  loadListings();
  loadWatchlist();
  renderReviewCard();
}

async function loadWatchlistsMeta() {
  state.watchlists = await api("/api/watchlists");
  if (!state.defaultWatchlistId && state.watchlists.length) state.defaultWatchlistId = state.watchlists[0].id;
  renderDefaultWatchlistSelect();
}

function renderDefaultWatchlistSelect() {
  const select = $("#default-watchlist");
  if (!select) return;
  select.innerHTML = state.watchlists.map((watchlist) => `
    <option value="${watchlist.id}">${escapeHtml(watchlist.name)} (${watchlist.listing_count || 0})</option>
  `).join("");
  if (state.defaultWatchlistId) select.value = String(state.defaultWatchlistId);
}

async function createWatchlistFromSettings() {
  const input = $("#new-watchlist-name");
  const name = input.value.trim();
  if (!name) {
    input.focus();
    return;
  }
  const watchlist = await api("/api/watchlists", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  input.value = "";
  state.defaultWatchlistId = watchlist.id;
  await loadWatchlistsMeta();
  await saveSettings();
  toast(t("toast.watchlistCreated"));
}

async function loadUsers() {
  if (!isAdmin()) {
    state.users = [];
    $("#users-list").innerHTML = "";
    return;
  }
  state.users = await api("/api/users");
  $("#users-list").innerHTML = state.users.map((user) => `
    <article class="user-card" data-user-id="${user.id}">
      <div>
        <strong>${escapeHtml(user.username)}</strong>
        <p class="meta">${escapeHtml(roleLabel(user.role))} · ${escapeHtml(user.enabled ? t("settings.enabled") : t("settings.disabled"))}</p>
      </div>
      <button class="mini-button" type="button" data-user-edit="${user.id}">${escapeHtml(t("settings.editUser"))}</button>
    </article>
  `).join("");
  $("#users-list").querySelectorAll("[data-user-edit]").forEach((button) => {
    button.addEventListener("click", () => {
      const user = state.users.find((item) => item.id === Number(button.dataset.userEdit));
      editUser(user);
    });
  });
}

function editUser(user) {
  $("#user-id").value = user?.id || "";
  $("#user-username").value = user?.username || "";
  $("#user-username").disabled = Boolean(user);
  $("#user-role").value = user?.role || "user";
  $("#user-enabled").checked = user ? Boolean(user.enabled) : true;
  $("#user-password").value = "";
  $("#user-password").required = !user;
  $("#save-user-button").textContent = t(user ? "settings.saveUser" : "settings.createUser");
  $("#delete-user-button").classList.toggle("hidden", !user);
}

async function saveUser() {
  const id = $("#user-id").value;
  const payload = {
    role: $("#user-role").value,
    enabled: $("#user-enabled").checked,
    password: $("#user-password").value,
  };
  if (id) {
    await api(`/api/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  } else {
    await api("/api/users", {
      method: "POST",
      body: JSON.stringify({
        username: $("#user-username").value,
        password: $("#user-password").value,
        role: payload.role,
        enabled: payload.enabled,
      }),
    });
  }
  toast(t("toast.userSaved"));
  editUser(null);
  await loadUsers();
}

async function deleteSelectedUser() {
  const id = $("#user-id").value;
  if (!id) return;
  await api(`/api/users/${id}`, { method: "DELETE" });
  toast(t("toast.userDeleted"));
  editUser(null);
  await loadUsers();
}

function roleLabel(role) {
  return role === "admin" ? t("settings.roleAdmin") : t("settings.roleUser");
}

function updateAiProviderHints() {
  const provider = $("#ai-provider").value;
  const baseUrl = $("#ai-base-url");
  const model = $("#ai-model");
  baseUrl.placeholder = {
    openai: "https://api.openai.com/v1",
    ollama: "http://host.docker.internal:11434/v1",
    lmstudio: "http://host.docker.internal:1234/v1",
  }[provider] || "https://api.openai.com/v1";
  model.placeholder = {
    openai: "gpt-4o-mini",
    ollama: "llama3.1",
    lmstudio: "local-model",
  }[provider] || "gpt-4o-mini";
}

async function testTelegram() {
  await api("/api/settings/telegram/test", { method: "POST" });
  toast(t("toast.telegramSent"));
}

async function testWebhook() {
  await api("/api/settings/webhook/test", { method: "POST" });
  toast(t("toast.webhookSent"));
}

async function testAiProvider() {
  const button = $("#ai-test-button");
  button.disabled = true;
  try {
    await saveSettings();
    await api("/api/ai/test", { method: "POST" });
    toast(t("toast.aiTestOk"));
  } catch (error) {
    toast(errorMessage(error));
  } finally {
    button.disabled = false;
  }
}

function addGuidedFilterRule() {
  const type = $("#filter-rule-type").value;
  const term = normalizeFilterTerm($("#filter-rule-term").value);
  const selector = {
    include: "#profile-include",
    required: "#profile-required",
    exclude: "#profile-exclude",
  }[type];
  if (!selector || !term) return;
  addListValue($(selector), term);
  $("#filter-rule-term").value = "";
  renderGuidedFilterRules();
  updateFilterPreview();
}

function renderGuidedFilterRules() {
  const target = $("#guided-filter-rules");
  if (!target) return;
  const rules = [
    ...lines("#profile-required").map((term) => ({ type: "required", term })),
    ...lines("#profile-exclude").map((term) => ({ type: "exclude", term })),
    ...lines("#profile-include").map((term) => ({ type: "include", term })),
  ];
  if (!rules.length) {
    target.innerHTML = `<p class="empty-filter-rules">${escapeHtml(t("filter.empty"))}</p>`;
    return;
  }
  target.innerHTML = rules.map((rule) => `
    <article class="guided-filter-rule ${escapeAttribute(rule.type)}">
      <span>${escapeHtml(guidedFilterSentence(rule))}</span>
      <button type="button" data-filter-remove-type="${escapeAttribute(rule.type)}" data-filter-remove-term="${escapeAttribute(rule.term)}" aria-label="${escapeAttribute(t("keyword.remove", { item: rule.term }))}">X</button>
    </article>
  `).join("");
  target.querySelectorAll("[data-filter-remove-type]").forEach((button) => {
    button.addEventListener("click", () => {
      removeListValue($(filterSelector(button.dataset.filterRemoveType)), button.dataset.filterRemoveTerm);
      renderGuidedFilterRules();
      updateFilterPreview();
    });
  });
}

function guidedFilterSentence(rule) {
  return t(`filter.${rule.type}Rule`, { term: rule.term });
}

function filterSelector(type) {
  return {
    include: "#profile-include",
    required: "#profile-required",
    exclude: "#profile-exclude",
  }[type];
}

function normalizeFilterTerm(value) {
  return String(value || "").trim().replace(/^\*+|\*+$/g, "").trim();
}

function setupChipInputs() {
  $$("textarea[data-chip-list]").forEach((textarea) => {
    if (textarea.dataset.chipReady) return;
    textarea.dataset.chipReady = "true";
    textarea.classList.add("chip-source");

    const control = document.createElement("div");
    control.className = "chip-list-control";
    control.innerHTML = `
      <div class="chip-list"></div>
      <input class="chip-list-input" type="text" autocomplete="off">
    `;
    textarea.insertAdjacentElement("afterend", control);

    const input = control.querySelector(".chip-list-input");
    control.addEventListener("click", () => input.focus());
    textarea.addEventListener("input", () => renderChipInput(textarea));
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === "," || event.key === "Tab") {
        if (input.value.trim()) {
          event.preventDefault();
          addChipValues(textarea, input.value);
          input.value = "";
        }
      }
      if (event.key === "Backspace" && !input.value) {
        removeChipValue(textarea, listFromText(textarea.value).at(-1));
      }
    });
    input.addEventListener("paste", () => {
      window.setTimeout(() => {
        if (input.value.includes("\n") || input.value.includes(",")) {
          addChipValues(textarea, input.value);
          input.value = "";
        }
      }, 0);
    });
    input.addEventListener("blur", () => {
      if (input.value.trim()) {
        addChipValues(textarea, input.value);
        input.value = "";
      }
    });
    renderChipInput(textarea);
  });
}

function syncAllChipInputs() {
  $$("textarea[data-chip-list]").forEach(renderChipInput);
}

function renderChipInput(textarea) {
  const control = textarea.nextElementSibling;
  if (!control?.classList.contains("chip-list-control")) return;
  const items = listFromText(textarea.value);
  const list = control.querySelector(".chip-list");
  const input = control.querySelector(".chip-list-input");
  list.innerHTML = items.map((item) => `
    <span class="keyword-chip">
      <span>${escapeHtml(item)}</span>
      <button type="button" data-chip-remove="${escapeAttribute(item)}" aria-label="${escapeAttribute(t("keyword.remove", { item }))}">X</button>
    </span>
  `).join("");
  list.querySelectorAll("[data-chip-remove]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      removeChipValue(textarea, button.dataset.chipRemove);
    });
  });
  input.placeholder = items.length ? "" : t(textarea.dataset.chipPlaceholder || "keyword.add");
}

function addChipValues(textarea, rawValue) {
  addListValue(textarea, rawValue);
}

function addListValue(textarea, rawValue) {
  const current = listFromText(textarea.value);
  const seen = new Set(current.map((item) => item.toLocaleLowerCase()));
  for (const item of listFromText(rawValue)) {
    const key = item.toLocaleLowerCase();
    if (!seen.has(key)) {
      current.push(item);
      seen.add(key);
    }
  }
  textarea.value = current.join("\n");
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
}

function removeChipValue(textarea, item) {
  removeListValue(textarea, item);
}

function removeListValue(textarea, item) {
  if (!item) return;
  textarea.value = listFromText(textarea.value).filter((value) => value !== item).join("\n");
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
}

function listFromText(value) {
  return String(value || "").split(/\n|,/).map((item) => item.trim()).filter(Boolean);
}

function lines(selector) {
  return listFromText($(selector).value);
}

function numberOrNull(selector) {
  const value = $(selector).value;
  return value === "" ? null : Number(value);
}

function formatDate(value) {
  if (!value) return t("date.never");
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return t("date.never");
  const locale = state.language === "de" ? "de-DE" : "en-US";
  return new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: state.language !== "de",
  }).format(date);
}

function setLanguage(language) {
  state.language = language === "de" ? "de" : "en";
  localStorage.setItem("marketplacelens.language", state.language);
  syncPreferenceControls();
  applyTranslations();
  const activeView = $(".view.active")?.id?.replace("-view", "") || "dashboard";
  $("#view-title").textContent = t({
    dashboard: "nav.dashboard",
    profiles: "nav.profiles",
    listings: "nav.listings",
    review: "nav.review",
    watchlist: "nav.watchlist",
    settings: "nav.settings",
  }[activeView]);
  updateProfileFormTitle();
  updateWizardCategories();
  updateFilterPreview();
  loadSummary();
  loadProfiles();
  loadListings();
  loadWatchlist();
  loadReviewQueue();
  loadUsers();
}

function setTheme(theme) {
  state.theme = theme === "dark" ? "dark" : "light";
  localStorage.setItem("marketplacelens.theme", state.theme);
  applyTheme();
}

function applyTheme() {
  document.body.dataset.theme = state.theme === "dark" ? "dark" : "light";
  document.documentElement.style.colorScheme = state.theme === "dark" ? "dark" : "light";
  syncPreferenceControls();
}

function applyTranslations() {
  document.documentElement.lang = state.language;
  $$("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  $$("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = t(node.dataset.i18nPlaceholder);
  });
  $$("[data-listing-view='list']").forEach((button) => {
    button.title = t("view.list");
    button.setAttribute("aria-label", t("view.list"));
  });
  $$("[data-listing-view='grid']").forEach((button) => {
    button.title = t("view.tiles");
    button.setAttribute("aria-label", t("view.tiles"));
  });
  const scanButton = $("#listing-scan-button");
  if (scanButton) {
    scanButton.title = t("view.scan");
    scanButton.setAttribute("aria-label", t("view.scan"));
  }
  updateListingRunButton();
  syncPreferenceControls();
  syncAllChipInputs();
  renderGuidedFilterRules();
}

function syncPreferenceControls() {
  $("#language-select").value = state.language;
  const themeToggle = $("#theme-toggle");
  if (themeToggle) {
    themeToggle.textContent = state.theme === "dark" ? "☀" : "☾";
    themeToggle.setAttribute("aria-label", state.theme === "dark" ? t("theme.switchToLight") : t("theme.switchToDark"));
  }
}

function t(key, values = {}) {
  const template = translations[state.language]?.[key] || translations.en[key] || key || "";
  return template.replace(/\{(\w+)\}/g, (_, name) => values[name] ?? "");
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, "&#096;");
}

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("visible");
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => node.classList.remove("visible"), 3600);
}

function debounce(callback, delay) {
  let timer;
  return () => {
    clearTimeout(timer);
    timer = setTimeout(callback, delay);
  };
}
