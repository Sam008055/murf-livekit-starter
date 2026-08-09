import React, { useEffect, useState } from 'react';
import {
  ChevronDown,
  Globe,
  MapPin,
  Mic,
  Phone,
  ShieldCheck,
  Sparkles,
  Sprout,
  User,
  Zap,
} from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  hasEnded?: boolean;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  hasEnded = false,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [farmer, setFarmer] = useState({
    farmer_id: '9876543210',
    name: 'Rajesh Kumar',
    district: 'Raigad',
    crop: 'Wheat',
  });

  useEffect(() => {
    const saved = localStorage.getItem('khetify_farmer_profile');
    if (saved) {
      try {
        setFarmer(JSON.parse(saved));
      } catch {
        // fallback to default
      }
    }
  }, []);

  const handleInputChange = (field: string, val: string) => {
    const updated = { ...farmer, [field]: val };
    setFarmer(updated);
    localStorage.setItem('khetify_farmer_profile', JSON.stringify(updated));
  };

  const handleStart = () => {
    localStorage.setItem('khetify_farmer_profile', JSON.stringify(farmer));
    onStartCall();
  };

  return (
    <div
      ref={ref}
      className="bg-background text-foreground selection:bg-primary/30 relative w-full overflow-x-hidden"
    >
      {/* Animated Glowing Orbs Background */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.15, 0.25, 0.15],
            x: [0, 50, 0],
            y: [0, -30, 0],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
          className="bg-primary/20 absolute -top-1/4 -left-1/4 h-[50vw] w-[50vw] rounded-full blur-[100px]"
        />
        <motion.div
          animate={{ scale: [1, 1.3, 1], opacity: [0.1, 0.2, 0.1], x: [0, -50, 0], y: [0, 50, 0] }}
          transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute top-1/2 -right-1/4 h-[40vw] w-[40vw] rounded-full bg-green-500/10 blur-[120px]"
        />
      </div>

      {/* Decorative noise texture */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-10 mix-blend-overlay"
        style={{
          backgroundImage:
            'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")',
        }}
      ></div>

      {/* Hero Section */}
      <div className="relative z-10 flex min-h-[90vh] w-full flex-col items-center justify-center px-4 pt-20 pb-12 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="bg-primary/10 border-primary/20 text-primary mb-8 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium"
        >
          <Sparkles className="h-4 w-4" />
          <span>Next-Generation Voice AI</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
          className="text-foreground mb-6 font-serif text-5xl font-bold tracking-tight md:text-7xl lg:text-8xl"
        >
          Welcome to{' '}
          <span className="from-primary bg-gradient-to-r to-green-500 bg-clip-text text-transparent">
            Khetify
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4, ease: 'easeOut' }}
          className="text-muted-foreground mx-auto max-w-2xl font-sans text-xl leading-relaxed md:text-2xl"
        >
          Your intelligent agricultural companion. Empowering farmers with instant, voice-first
          knowledge in Hindi and English.
        </motion.p>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.5 }}
          className="text-muted-foreground/60 hover:text-primary absolute bottom-10 flex cursor-pointer flex-col items-center transition-colors"
          onClick={() => {
            window.scrollTo({ top: window.innerHeight * 0.9, behavior: 'smooth' });
          }}
        >
          <span className="mb-3 text-xs font-semibold tracking-[0.2em] uppercase">
            Discover More
          </span>
          <ChevronDown className="h-5 w-5 animate-bounce" />
        </motion.div>
      </div>

      {/* Tech Stack / Features Section */}
      <div className="relative z-10 w-full bg-black/5 px-4 py-24 dark:bg-white/5">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.6 }}
            className="mb-16 text-center"
          >
            <h2 className="mb-6 font-serif text-3xl font-bold md:text-5xl">Powered by the best</h2>
            <p className="text-muted-foreground mx-auto max-w-2xl font-sans text-lg md:text-xl">
              We&apos;ve combined state-of-the-art AI models to create a seamless, real-time
              conversational experience tailored for agriculture.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {[
              {
                title: 'LiveKit',
                desc: 'Ultra low-latency WebRTC infrastructure for instant voice transmission.',
                icon: Zap,
              },
              {
                title: 'Google Gemini & RAG',
                desc: 'Advanced reasoning over official agricultural knowledge base.',
                icon: Globe,
              },
              {
                title: 'Deepgram & Murf',
                desc: 'Lightning-fast speech recognition and lifelike Hindi text-to-speech.',
                icon: Mic,
              },
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
              >
                <Card className="bg-background/40 border-primary/10 shadow-lg backdrop-blur-xl transition-transform duration-300 hover:-translate-y-2">
                  <CardHeader>
                    <div className="bg-primary/10 text-primary mb-4 flex h-12 w-12 items-center justify-center rounded-2xl">
                      <feature.icon className="h-6 w-6" />
                    </div>
                    <CardTitle className="text-xl font-semibold">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-foreground/70 text-base leading-relaxed">
                      {feature.desc}
                    </CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Connect Card Section with Farmer Profile */}
      <div className="relative z-10 flex w-full flex-col items-center justify-center px-4 py-24">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="w-full max-w-2xl"
        >
          <div className="from-primary/30 to-primary/5 relative rounded-3xl bg-gradient-to-b p-1 shadow-2xl">
            <div className="bg-background relative flex flex-col items-center overflow-hidden rounded-[22px] px-6 py-10 text-center md:p-12">
              {/* Subtle background glow inside card */}
              <div className="bg-primary/5 pointer-events-none absolute top-0 left-1/2 h-1/2 w-full -translate-x-1/2 rounded-full blur-3xl" />

              <h2 className="text-foreground relative z-10 mb-3 font-serif text-3xl font-bold tracking-tight md:text-5xl">
                {hasEnded ? 'Session Ended' : 'Start Your Session'}
              </h2>

              <p className="text-muted-foreground relative z-10 mx-auto mb-8 max-w-md font-sans text-base md:text-lg">
                {hasEnded
                  ? 'The conversation has been closed. Click below if you have more questions.'
                  : 'Enter your farmer identity below so Khetify remembers your field facts.'}
              </p>

              {/* Farmer Memory Profile Form */}
              <div className="bg-primary/5 border-primary/20 relative z-10 mb-8 w-full max-w-lg rounded-2xl border p-5 text-left backdrop-blur-md">
                <div className="text-primary mb-4 flex items-center gap-2 text-sm font-semibold">
                  <ShieldCheck className="h-4.5 w-4.5 text-green-500" />
                  <span>Farmer Profile Memory</span>
                </div>

                <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
                  <div>
                    <label className="text-muted-foreground mb-1.5 flex items-center gap-1.5 text-xs font-medium">
                      <User className="text-primary h-3.5 w-3.5" /> Farmer Name
                    </label>
                    <input
                      type="text"
                      value={farmer.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="e.g. Rajesh Kumar"
                      className="bg-background/90 border-border focus:ring-primary text-foreground w-full rounded-xl border px-3.5 py-2 text-sm font-medium transition-all focus:ring-2 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-muted-foreground mb-1.5 flex items-center gap-1.5 text-xs font-medium">
                      <Phone className="text-primary h-3.5 w-3.5" /> Phone / Farmer ID
                    </label>
                    <input
                      type="text"
                      value={farmer.farmer_id}
                      onChange={(e) => handleInputChange('farmer_id', e.target.value)}
                      placeholder="e.g. 9876543210"
                      className="bg-background/90 border-border focus:ring-primary text-foreground w-full rounded-xl border px-3.5 py-2 text-sm font-medium transition-all focus:ring-2 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-muted-foreground mb-1.5 flex items-center gap-1.5 text-xs font-medium">
                      <MapPin className="text-primary h-3.5 w-3.5" /> District / Region
                    </label>
                    <input
                      type="text"
                      value={farmer.district}
                      onChange={(e) => handleInputChange('district', e.target.value)}
                      placeholder="e.g. Raigad"
                      className="bg-background/90 border-border focus:ring-primary text-foreground w-full rounded-xl border px-3.5 py-2 text-sm font-medium transition-all focus:ring-2 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-muted-foreground mb-1.5 flex items-center gap-1.5 text-xs font-medium">
                      <Sprout className="text-primary h-3.5 w-3.5" /> Primary Crop
                    </label>
                    <input
                      type="text"
                      value={farmer.crop}
                      onChange={(e) => handleInputChange('crop', e.target.value)}
                      placeholder="e.g. Wheat"
                      className="bg-background/90 border-border focus:ring-primary text-foreground w-full rounded-xl border px-3.5 py-2 text-sm font-medium transition-all focus:ring-2 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="relative z-10">
                <Button
                  size="lg"
                  onClick={handleStart}
                  className="hover:shadow-primary/25 bg-primary text-primary-foreground h-14 rounded-full px-8 text-lg font-semibold tracking-wide shadow-xl transition-all duration-300 hover:-translate-y-1"
                >
                  <Mic className="mr-2 h-5 w-5" />
                  {startButtonText}
                </Button>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="border-border/40 text-muted-foreground/60 w-full border-t py-8 text-center text-sm">
        <p>Built for the Voice for Bharat Challenge &bull; 2026</p>
      </div>
    </div>
  );
};
