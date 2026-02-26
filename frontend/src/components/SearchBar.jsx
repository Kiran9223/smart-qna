import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

export default function SearchBar() {
  const [searchParams] = useSearchParams();
  const [value, setValue] = useState(searchParams.get("search") || "");
  const navigate = useNavigate();

  const doSearch = useCallback(
    debounce((q) => {
      const params = new URLSearchParams();
      if (q) params.set("search", q);
      navigate(`/?${params.toString()}`);
    }, 300),
    [navigate]
  );

  const handleChange = (e) => {
    setValue(e.target.value);
    doSearch(e.target.value);
  };

  return (
    <div className="relative">
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        type="text"
        placeholder="Search questions..."
        value={value}
        onChange={handleChange}
        className="input pl-10 w-full"
      />
    </div>
  );
}
