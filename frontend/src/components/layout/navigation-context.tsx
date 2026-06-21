'use client';

import { createContext, useCallback, useContext, useState } from 'react';

interface NavigationKontext {
  mobileOffen: boolean;
  oeffnen: () => void;
  schliessen: () => void;
  umschalten: () => void;
}

const Standard: NavigationKontext = {
  mobileOffen: false,
  oeffnen: () => {},
  schliessen: () => {},
  umschalten: () => {},
};

const Ctx = createContext<NavigationKontext>(Standard);

export function NavigationProvider({ children }: { children: React.ReactNode }) {
  const [mobileOffen, setMobileOffen] = useState(false);
  const oeffnen = useCallback(() => setMobileOffen(true), []);
  const schliessen = useCallback(() => setMobileOffen(false), []);
  const umschalten = useCallback(() => setMobileOffen((v) => !v), []);
  return (
    <Ctx.Provider value={{ mobileOffen, oeffnen, schliessen, umschalten }}>
      {children}
    </Ctx.Provider>
  );
}

export function useNavigation(): NavigationKontext {
  return useContext(Ctx);
}
