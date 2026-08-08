import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { motion, useScroll, useTransform } from 'motion/react';
import { ChevronDown } from 'lucide-react';

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
    <div ref={ref} className="relative w-full bg-background text-foreground overflow-x-hidden">
      {/* Animated Glowing Orbs Background */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.2, 0.4, 0.2],
          x: [0, 100, 0],
          y: [0, -50, 0],
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        className="fixed top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[100px] pointer-events-none z-0"
      />
      <motion.div
        animate={{
          scale: [1, 1.5, 1],
          opacity: [0.15, 0.3, 0.15],
          x: [0, -100, 0],
          y: [0, 100, 0],
        }}
        transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
        className="fixed bottom-1/4 right-1/4 w-[30rem] h-[30rem] bg-green-500/10 rounded-full blur-[120px] pointer-events-none z-0"
      />

      {/* Decorative background elements */}
      <div className="fixed inset-0 opacity-20 pointer-events-none z-0" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }}></div>
      <div className="fixed top-0 left-0 w-full h-32 bg-gradient-to-b from-primary/10 to-transparent pointer-events-none z-0"></div>
      
      {/* Hero Section (Page 1) */}
      <div className="relative z-10 w-full min-h-screen flex flex-col items-center justify-center text-center px-4 pt-12 pb-24">
        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
          className="font-serif text-5xl md:text-7xl font-semibold tracking-tight text-primary mb-4 drop-shadow-sm"
        >
          Khetify
        </motion.h1>
        
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.6 }}
          className="font-sans text-muted-foreground text-xl md:text-2xl font-light italic"
        >
          The future of heritage farming.
        </motion.p>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.5, ease: "easeOut", delay: 1.2 }}
          className="mt-8 font-sans text-foreground/80 text-lg md:text-xl font-medium max-w-lg mx-auto leading-relaxed"
        >
          Your AI agricultural assistant. <br/> 
          Scroll down to ask questions about crops, fertilizers, and farming best practices.
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 2 }}
          className="absolute bottom-12 flex flex-col items-center animate-bounce text-primary/70"
        >
          <span className="text-sm uppercase tracking-widest font-semibold mb-2">Scroll to Connect</span>
          <ChevronDown className="w-6 h-6" />
        </motion.div>
      </div>

      {/* Features / Tech Stack Section */}
      <div className="relative z-20 w-full min-h-[50vh] flex flex-col items-center justify-center px-4 py-20">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <h2 className="font-serif text-3xl md:text-4xl font-semibold text-primary/80 mb-4">Powered by Advanced AI</h2>
          <p className="font-sans text-muted-foreground text-lg max-w-2xl mx-auto">
            Khetify brings the latest in voice and conversational technology to the fields of Bharat.
          </p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {/* Feature 1 */}
          <Card className="bg-card/50 border-primary/10 shadow-lg backdrop-blur-md hover:bg-card/70 transition-colors duration-300">
            <CardHeader>
              <CardTitle className="text-xl font-serif text-primary">LiveKit</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base text-foreground/70">
                Lightning-fast WebRTC infrastructure for real-time, low-latency voice communication.
              </CardDescription>
            </CardContent>
          </Card>

          {/* Feature 2 */}
          <Card className="bg-card/50 border-primary/10 shadow-lg backdrop-blur-md hover:bg-card/70 transition-colors duration-300">
            <CardHeader>
              <CardTitle className="text-xl font-serif text-primary">Murf AI</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base text-foreground/70">
                High-fidelity, ultra-realistic Hindi text-to-speech engine capturing authentic linguistic nuances.
              </CardDescription>
            </CardContent>
          </Card>

          {/* Feature 3 */}
          <Card className="bg-card/50 border-primary/10 shadow-lg backdrop-blur-md hover:bg-card/70 transition-colors duration-300">
            <CardHeader>
              <CardTitle className="text-xl font-serif text-primary">Google Gemini</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base text-foreground/70">
                Advanced conversational intelligence powering accurate, contextual, and safe agricultural advice.
              </CardDescription>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Connect Card Section (Page 2) */}
      <div className="relative z-20 w-full min-h-[50vh] flex flex-col items-center justify-start px-4 pb-20">
        <motion.div 
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="w-full max-w-xl"
        >
          <Card className="bg-card/70 backdrop-blur-md border-border shadow-2xl rounded-3xl overflow-hidden px-2 py-4">
            <CardHeader className="flex flex-col items-center text-center pb-2">
              <CardTitle className="font-serif text-4xl font-semibold tracking-tight text-primary mb-2">
                {hasEnded ? 'Session ended' : 'Ready to Connect'}
              </CardTitle>
            </CardHeader>

            <CardContent className="text-center pt-2">
              <CardDescription className="font-sans text-muted-foreground text-lg leading-relaxed max-w-md mx-auto">
                {hasEnded 
                  ? 'The conversation is over. Would you like to start again?' 
                  : 'Begin your session with Khetify. Speak naturally in Hindi for crop guidance and insights.'}
              </CardDescription>
            </CardContent>
            
            <CardFooter className="flex justify-center pt-6 pb-4">
              <Button
                size="lg"
                onClick={onStartCall}
                className="w-64 rounded-full font-serif text-sm font-semibold tracking-widest uppercase shadow-lg hover:shadow-xl transition-all duration-300 bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {startButtonText}
              </Button>
            </CardFooter>
          </Card>
        </motion.div>
      </div>

      <div className="fixed bottom-8 left-0 flex w-full items-center justify-center z-10 pointer-events-none">
        <p className="text-muted-foreground text-xs tracking-wider uppercase font-sans">
          Est. 2026 &bull; Voice for Bharat
        </p>
      </div>
    </div>
  );
};
