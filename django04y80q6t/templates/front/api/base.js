const normalizeUrl = (url) => {
	if (!url) return "http://localhost:8080/django04y80q6t/"
	return url.endsWith('/') ? url : `${url}/`
}

const envBaseUrl = typeof process !== 'undefined' && process.env ? process.env.VUE_APP_BASE_API : ''

const base = {
	url: normalizeUrl(envBaseUrl || "http://localhost:8080/django04y80q6t/"),
}

export default base
