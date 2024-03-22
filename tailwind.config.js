/** @type {import('tailwindcss').Config} */
module.exports = {
	content: ["./frontend/dynamic/**/*.{html,js}", "./node_modules/flowbite/**/*.js"],
	theme: {
		extend: {},
	},
	darkMode: "class",
	plugins: [require("flowbite/plugin")],
};
