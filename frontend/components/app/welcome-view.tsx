import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { motion, useScroll, useTransform } from 'motion/react';
import { ChevronDown } from 'lucide-react';
import Spline from '@splinetool/react-spline';

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
  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.3], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.3], [1, 0.95]);
  const cardOpacity = useTransform(scrollYProgress, [0.3, 0.7], [0, 1]);
  const cardY = useTransform(scrollYProgress, [0.3, 0.7], [50, 0]);

  return (
    <div ref={ref} className="relative w-full bg-background text-foreground min-h-[150vh]">
      {/* 3D Spline Background */}
      <div className="fixed inset-0 z-0">
        <Spline scene="https://prod.spline.design/q6LzVjY0YtYmC6b2/scene.splinecode" />
      </div>

      {/* Decorative background elements */}
      <div className="fixed inset-0 opacity-20 pointer-events-none z-0" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }}></div>
      <div className="fixed top-0 left-0 w-full h-32 bg-gradient-to-b from-primary/10 to-transparent pointer-events-none z-0"></div>
      
      {/* Hero Section */}
      <motion.div 
        style={{ opacity: heroOpacity, scale: heroScale }}
        className="fixed inset-0 flex flex-col items-center justify-center text-center pointer-events-none z-10"
      >
        <h1 className="font-serif text-5xl md:text-7xl font-semibold tracking-tight text-primary mb-4 drop-shadow-sm">
          Khetify
        </h1>
        <p className="font-sans text-muted-foreground text-xl md:text-2xl font-light italic">
          The future of heritage farming.
        </p>
        
        <div className="absolute bottom-12 flex flex-col items-center animate-bounce text-primary/70">
          <span className="text-sm uppercase tracking-widest font-semibold mb-2">Scroll to Connect</span>
          <ChevronDown className="w-6 h-6" />
        </div>
      </motion.div>

      {/* Connect Card Section */}
      <div className="absolute top-[100vh] w-full flex justify-center pb-[20vh] px-4">
        <motion.div style={{ opacity: cardOpacity, y: cardY }} className="w-full max-w-xl z-20">
          <Card className="bg-card/70 backdrop-blur-md border-border shadow-2xl rounded-3xl overflow-hidden px-2 py-4">
            <CardHeader className="flex flex-col items-center text-center pb-2">
              <CardTitle className="font-serif text-4xl font-semibold tracking-tight text-primary mb-2">
                {hasEnded ? 'Call ended' : 'Ready'}
              </CardTitle>
            </CardHeader>

            <CardContent className="text-center pt-2">
              <CardDescription className="font-sans text-muted-foreground text-lg leading-relaxed max-w-md mx-auto">
                {hasEnded 
                  ? 'The conversation is over. Would you like to start again?' 
                  : 'Begin your session with Khetify. Speak naturally for crop guidance and insights.'}
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
