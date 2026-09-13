"use client";

import { useLeadTriageNavigation } from "../context/LeadTriageNavigationContext";
import type { ScreenId } from "../types";
import { EscalationScreen } from "./EscalationScreen";
import { EvalScreen } from "./EvalScreen";
import { FeedScreen } from "./FeedScreen";
import { IntegrationsScreen } from "./IntegrationsScreen";
import { RegistryScreen } from "./RegistryScreen";
import { RunDetailScreen } from "./RunDetailScreen";
import type { ComponentType } from "react";

/** Open/closed: add a screen by registering it here without editing the shell. */
const SCREEN_COMPONENTS: Record<ScreenId, ComponentType> = {
  feed: FeedScreen,
  registry: RegistryScreen,
  detail: RunDetailScreen,
  eval: EvalScreen,
  escalation: EscalationScreen,
  settings: IntegrationsScreen,
};

export function ScreenRouter() {
  const { screen } = useLeadTriageNavigation();
  const ActiveScreen = SCREEN_COMPONENTS[screen];
  return <ActiveScreen />;
}
