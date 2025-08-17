// filepath: e:\work\IBM-Hackathon\jobswitch.ai\jobswitch-ui\jobswitch-ui\src\Header.js
import logo from "./logo.svg";
import "./App.css";

function Header() {
  return (
    <header className="bg-white shadow">
      <nav className="container mx-auto flex items-center justify-between p-4">
        <div className="text-2xl font-bold text-blue-600">JobSwitch</div>
        <ul className="flex space-x-6">
          <li>
            <a href="#" className="text-gray-700 hover:text-blue-600">
              Home
            </a>
          </li>
          <li>
            <a href="#" className="text-gray-700 hover:text-blue-600">
              About
            </a>
          </li>
          <li>
            <a href="#" className="text-gray-700 hover:text-blue-600">
              Contact
            </a>
          </li>
        </ul>
        <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Login
        </button>
      </nav>
    </header>
  );
}

export default Header;
