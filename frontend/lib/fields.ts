import {
  User,
  Mail,
  Linkedin,
  Facebook,
  Instagram,
  Building2,
  Globe,
  MapPin,
  Flag,
  Github,
  Twitter,
  Phone,
  type LucideIcon,
} from "lucide-react";
import type { OutputCategory, SearchInputs } from "./types";

export interface InputFieldDef {
  key: keyof SearchInputs;
  label: string;
  placeholder: string;
  icon: LucideIcon;
  group: "identity" | "handles" | "work";
}

export const INPUT_FIELDS: InputFieldDef[] = [
  { key: "full_name", label: "Full name", placeholder: "Jane Doe", icon: User, group: "identity" },
  { key: "email", label: "Email", placeholder: "jane@work.com", icon: Mail, group: "identity" },
  { key: "personal_email", label: "Personal email", placeholder: "jane@gmail.com", icon: Mail, group: "identity" },
  { key: "city", label: "City", placeholder: "Austin", icon: MapPin, group: "identity" },
  { key: "country", label: "Country", placeholder: "United States", icon: Flag, group: "identity" },

  { key: "linkedin", label: "LinkedIn", placeholder: "linkedin.com/in/janedoe", icon: Linkedin, group: "handles" },
  { key: "github", label: "GitHub", placeholder: "janedoe", icon: Github, group: "handles" },
  { key: "twitter", label: "Twitter / X", placeholder: "@janedoe", icon: Twitter, group: "handles" },
  { key: "facebook", label: "Facebook", placeholder: "facebook.com/jane.doe", icon: Facebook, group: "handles" },
  { key: "instagram", label: "Instagram", placeholder: "@janedoe", icon: Instagram, group: "handles" },

  { key: "company_name", label: "Company", placeholder: "Acme Corp", icon: Building2, group: "work" },
  { key: "company_website", label: "Company website", placeholder: "acme.com", icon: Globe, group: "work" },
];

export interface OutputCategoryDef {
  key: OutputCategory;
  label: string;
  icon: LucideIcon;
}

export const OUTPUT_CATEGORIES: OutputCategoryDef[] = [
  { key: "personal_email", label: "Personal email", icon: Mail },
  { key: "work_email", label: "Work email", icon: Mail },
  { key: "phone", label: "Phone", icon: Phone },
  { key: "linkedin", label: "LinkedIn", icon: Linkedin },
  { key: "github", label: "GitHub", icon: Github },
  { key: "twitter", label: "Twitter / X", icon: Twitter },
  { key: "facebook", label: "Facebook", icon: Facebook },
  { key: "instagram", label: "Instagram", icon: Instagram },
  { key: "personal_website", label: "Personal website", icon: Globe },
  { key: "company", label: "Company", icon: Building2 },
];
