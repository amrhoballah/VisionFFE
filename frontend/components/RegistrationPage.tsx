import React, { useState, useMemo } from 'react';
import { ImageIcon } from './Icons';
import { useAuth } from '../contexts/AuthContext';

interface RegistrationPageProps {
  onBackToHome: () => void;
  onNavigateToLogin: () => void;
}

// Updated country data to include Middle East and North African countries
const countryData: { [key: string]: string } = {
    "Algeria": "+213",
    "Australia": "+61",
    "Bahrain": "+973",
    "Brazil": "+55",
    "Canada": "+1",
    "Cyprus": "+357",
    "Egypt": "+20",
    "France": "+33",
    "Germany": "+49",
    "India": "+91",
    "Iran": "+98",
    "Iraq": "+964",
    "Japan": "+81",
    "Jordan": "+962",
    "Kuwait": "+965",
    "Lebanon": "+961",
    "Libya": "+218",
    "Morocco": "+212",
    "Oman": "+968",
    "Palestine": "+970",
    "Qatar": "+974",
    "Saudi Arabia": "+966",
    "Sudan": "+249",
    "Syria": "+963",
    "Tunisia": "+216",
    "Turkey": "+90",
    "United Arab Emirates": "+971",
    "United Kingdom": "+44",
    "United States": "+1",
    "Yemen": "+967",
    "Other": ""
};

// Sort countries alphabetically, but keep "Other" at the end.
const countries = Object.keys(countryData)
    .filter(c => c !== "Other")
    .sort()
    .concat("Other");

const RegistrationPage: React.FC<RegistrationPageProps> = ({ onBackToHome, onNavigateToLogin }) => {
    const [title, setTitle] = useState<'Office' | 'Freelancer' | 'Supplier' | ''>('');
    const [selectedCountry, setSelectedCountry] = useState('');
    const [error, setError] = useState<string | null>(null);
    const { register, isLoading } = useAuth();
    
    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);
        
        const formData = new FormData(e.currentTarget);
        const data = Object.fromEntries(formData.entries());

        const phoneInput = data.phone as string;
        const countryCode = countryData[data.location as keyof typeof countryData] || '';
        const fullPhoneNumber = phoneInput && countryCode ? `${countryCode}${phoneInput}` : phoneInput;

        // Extract required fields for backend registration
        const registrationData = {
            username: data.username as string,
            email: data.email as string,
            password: data.password as string,
        };

        try {
            await register(registrationData);
            // Registration successful - user is automatically logged in
            // The parent component will handle navigation to the main app
        } catch (err: any) {
            setError(err.message || 'Registration failed. Please try again.');
        }
    };

    const countryCode = useMemo(() => {
        return countryData[selectedCountry] || '';
    }, [selectedCountry]);

    const CustomRadio = ({ name, value, checked, onChange, label }: { name: string, value: string, checked: boolean, onChange: (e: React.ChangeEvent<HTMLInputElement>) => void, label: string }) => (
        <label className="flex items-center gap-3 cursor-pointer">
            <div className="relative flex items-center">
                <input 
                    type="radio" 
                    name={name} 
                    value={value} 
                    required 
                    checked={checked}
                    onChange={onChange} 
                    className="peer absolute opacity-0 w-full h-full cursor-pointer" 
                />
                <span className="w-5 h-5 border-2 border-base-content/50 rounded-full flex items-center justify-center peer-checked:border-brand-primary transition-colors">
                    <span className="w-2.5 h-2.5 rounded-full bg-brand-primary scale-0 peer-checked:scale-100 transition-transform"></span>
                </span>
            </div>
            <span>{label}</span>
        </label>
    );

    return (
        <div className="min-h-screen bg-base-100 text-base-content flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-2xl">
                <header className="text-center mb-8">
                    <div className="flex items-center justify-center gap-3 mb-2">
                        <ImageIcon className="w-8 h-8 text-brand-primary" />
                        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
                            Create Your Account
                        </h1>
                    </div>
                    <p className="text-base-content/70">
                        Join us to start extracting magic from your room photos.
                    </p>
                </header>

                <main className="bg-base-200 p-8 rounded-xl shadow-lg">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label htmlFor="firstName" className="block text-sm font-medium text-base-content/80 mb-2">First Name</label>
                                <input type="text" id="firstName" name="firstName" required className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition" />
                            </div>
                            <div>
                                <label htmlFor="lastName" className="block text-sm font-medium text-base-content/80 mb-2">Last Name</label>
                                <input type="text" id="lastName" name="lastName" required className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition" />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-base-content/80 mb-2">Username</label>
                            <input type="text" id="username" name="username" required className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition" />
                        </div>

                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-base-content/80 mb-2">Email</label>
                            <input type="email" id="email" name="email" required className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition" />
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-base-content/80 mb-2">Password</label>
                            <input type="password" id="password" name="password" required minLength={8} className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition" />
                            <p className="text-xs text-base-content/60 mt-1">Password must be at least 8 characters long</p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-base-content/80 mb-2">Title</label>
                            <div className="flex flex-wrap gap-6">
                                <CustomRadio 
                                    name="title" 
                                    value="Office" 
                                    label="Office"
                                    checked={title === 'Office'}
                                    onChange={(e) => setTitle(e.target.value as any)} 
                                />
                                <CustomRadio 
                                    name="title" 
                                    value="Freelancer" 
                                    label="Freelancer"
                                    checked={title === 'Freelancer'}
                                    onChange={(e) => setTitle(e.target.value as any)} 
                                />
                                <CustomRadio 
                                    name="title" 
                                    value="Supplier" 
                                    label="Supplier"
                                    checked={title === 'Supplier'}
                                    onChange={(e) => setTitle(e.target.value as any)} 
                                />
                            </div>
                        </div>

                        {title === 'Office' && (
                            <div className="transition-all duration-300 ease-in-out">
                                <label htmlFor="officeName" className="block text-sm font-medium text-base-content/80 mb-2">Office Name (Optional)</label>
                                <input type="text" id="officeName" name="officeName" className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition" />
                            </div>
                        )}

                        {title === 'Supplier' && (
                            <div className="transition-all duration-300 ease-in-out">
                                <label htmlFor="supplierName" className="block text-sm font-medium text-base-content/80 mb-2">Supplier Name</label>
                                <input type="text" id="supplierName" name="supplierName" required className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition" />
                            </div>
                        )}


                        <div>
                            <label htmlFor="location" className="block text-sm font-medium text-base-content/80 mb-2">Location (Country)</label>
                            <select 
                                id="location" 
                                name="location" 
                                required 
                                value={selectedCountry}
                                onChange={(e) => setSelectedCountry(e.target.value)}
                                className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition"
                            >
                                <option value="" disabled>Select a country</option>
                                {countries.map(country => <option key={country} value={country}>{country}</option>)}
                            </select>
                        </div>
                        
                        <div>
                            <label htmlFor="phone" className="block text-sm font-medium text-base-content/80 mb-2">Phone Number</label>
                            <div className="flex items-center w-full bg-base-300 border border-base-300 rounded-lg focus-within:ring-2 focus-within:ring-brand-primary focus-within:border-brand-primary transition">
                                <span className="pl-3 pr-2 text-base-content/70">{countryCode}</span>
                                <input 
                                    type="tel" 
                                    id="phone" 
                                    name="phone" 
                                    required 
                                    placeholder={selectedCountry ? "Your phone number" : "Select a country first"}
                                    disabled={!selectedCountry}
                                    className="w-full bg-transparent text-base-content p-2.5 outline-none disabled:cursor-not-allowed" 
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="text-center bg-red-900/50 border border-red-700 text-red-200 text-sm p-3 rounded-lg">
                                <p>{error}</p>
                            </div>
                        )}
                        
                        <div className="flex flex-col-reverse sm:flex-row items-center justify-between gap-4 pt-4">
                             <button
                                type="button"
                                onClick={onBackToHome}
                                className="w-full sm:w-auto px-6 py-3 text-sm font-semibold text-base-content bg-base-300 rounded-lg hover:bg-opacity-80 transition-all"
                            >
                                Back to Home
                            </button>
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full sm:w-auto px-8 py-3 font-semibold text-white bg-gradient-to-r from-brand-primary to-brand-secondary rounded-lg hover:scale-105 transform transition-transform duration-300 ease-in-out shadow-lg disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
                            >
                                {isLoading ? (
                                    <div className="w-5 h-5 border-2 border-white/50 border-t-white rounded-full animate-spin"></div>
                                ) : (
                                    'Create Account'
                                )}
                            </button>
                        </div>
                         <div className="text-center text-sm text-base-content/70 pt-2">
                            <p>
                                Already have an account?{' '}
                                <button type="button" onClick={onNavigateToLogin} className="font-medium text-brand-primary hover:underline">
                                    Log In
                                </button>
                            </p>
                        </div>
                    </form>
                </main>
            </div>
        </div>
    );
};

export default RegistrationPage;