import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { motion } from 'motion/react';
import { ChevronDown, Sparkles, Mic, Zap, Globe } from 'lucide-react';

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
  return (
    <div ref={ref} className="relative w-full bg-background text-foreground overflow-x-hidden selection:bg-primary/30">
      {/* Animated Glowing Orbs Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.15, 0.25, 0.15], x: [0, 50, 0], y: [0, -30, 0] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute -top-1/4 -left-1/4 w-[50vw] h-[50vw] bg-primary/20 rounded-full blur-[100px]"
        />
        <motion.div
          animate={{ scale: [1, 1.3, 1], opacity: [0.1, 0.2, 0.1], x: [0, -50, 0], y: [0, 50, 0] }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/2 -right-1/4 w-[40vw] h-[40vw] bg-green-500/10 rounded-full blur-[120px]"
        />
      </div>

      {/* Decorative noise texture */}
      <div className="fixed inset-0 opacity-10 pointer-events-none z-0 mix-blend-overlay" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }}></div>
      
      {/* Hero Section */}
      <div className="relative z-10 w-full min-h-[90vh] flex flex-col items-center justify-center text-center px-4 pt-20 pb-12">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-8"
        >
          <Sparkles className="w-4 h-4" />
          <span>Next-Generation Voice AI</span>
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="font-serif text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight text-foreground mb-6"
        >
          Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-green-500">Khetify</span>
        </motion.h1>
        
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
          className="font-sans text-muted-foreground text-xl md:text-2xl max-w-2xl mx-auto leading-relaxed"
        >
          Your intelligent agricultural companion. Empowering farmers with instant, voice-first knowledge in Hindi and English.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.5 }}
          className="absolute bottom-10 flex flex-col items-center text-muted-foreground/60 hover:text-primary transition-colors cursor-pointer"
          onClick={() => {
            window.scrollTo({ top: window.innerHeight * 0.9, behavior: 'smooth' });
          }}
        >
          <span className="text-xs uppercase tracking-[0.2em] font-semibold mb-3">Discover More</span>
          <ChevronDown className="w-5 h-5 animate-bounce" />
        </motion.div>
      </div>

      {/* Tech Stack / Features Section */}
      <div className="relative z-10 w-full bg-black/5 dark:bg-white/5 py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="font-serif text-3xl md:text-5xl font-bold mb-6">Powered by the best</h2>
            <p className="font-sans text-muted-foreground text-lg md:text-xl max-w-2xl mx-auto">
              We've combined state-of-the-art AI models to create a seamless, real-time conversational experience tailored for agriculture.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { title: "LiveKit", desc: "Ultra low-latency WebRTC infrastructure for instant voice transmission.", icon: Zap },
              { title: "Google Gemini", desc: "Advanced reasoning for accurate and safe agricultural advice.", icon: Globe },
              { title: "Deepgram & Murf", desc: "Lightning-fast speech recognition and lifelike Hindi text-to-speech.", icon: Mic },
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
              >
                <Card className="bg-background/40 border-primary/10 shadow-lg backdrop-blur-xl hover:-translate-y-2 transition-transform duration-300">
                  <CardHeader>
                    <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 text-primary">
                      <feature.icon className="w-6 h-6" />
                    </div>
                    <CardTitle className="text-xl font-semibold">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-base text-foreground/70 leading-relaxed">
                      {feature.desc}
                    </CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Connect Card Section */}
      <div className="relative z-10 w-full py-32 px-4 flex flex-col items-center justify-center">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="w-full max-w-2xl"
        >
          <div className="relative p-1 rounded-3xl bg-gradient-to-b from-primary/30 to-primary/5 shadow-2xl">
            <div className="bg-background rounded-[22px] px-6 py-12 md:p-16 text-center flex flex-col items-center relative overflow-hidden">
              
              {/* Subtle background glow inside card */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1/2 bg-primary/5 blur-3xl rounded-full pointer-events-none" />

              <h2 className="font-serif text-3xl md:text-5xl font-bold tracking-tight text-foreground mb-4 relative z-10">
                {hasEnded ? 'Session Ended' : 'Start Your Session'}
              </h2>
              
              <p className="font-sans text-muted-foreground text-lg mb-10 max-w-md mx-auto relative z-10">
                {hasEnded 
                  ? 'The conversation has been closed. Click below if you have more questions.' 
                  : 'Tap the button below to connect with Khetify. Speak naturally and get instant advice.'}
              </p>
              
              <div className="relative z-10">
                <Button
                  size="lg"
                  onClick={onStartCall}
                  className="h-14 px-8 rounded-full font-semibold text-lg tracking-wide shadow-xl hover:shadow-primary/25 hover:-translate-y-1 transition-all duration-300 bg-primary text-primary-foreground"
                >
                  <Mic className="w-5 h-5 mr-2" />
                  {startButtonText}
                </Button>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="w-full py-8 text-center border-t border-border/40 text-muted-foreground/60 text-sm">
        <p>Built for the Voice for Bharat Challenge &bull; 2026</p>
      </div>
    </div>
  );
};
