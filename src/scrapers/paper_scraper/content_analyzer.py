import logging
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

from src.services.llm_service import LLMService
from .config import paper_scraper_settings

class PaperContentAnalyzer:
    """
    Analyzer for academic paper content using LLM services
    """

    def __init__(self, llm_service: LLMService = None):
        self.logger = logging.getLogger(__name__)
        self.llm_service = llm_service or LLMService()
        self.settings = paper_scraper_settings

    async def analyze_paper(
        self,
        paper_data: Dict[str, Any],
        extract_keywords: bool = True,
        generate_summary: bool = True,
        analyze_citations: bool = True,
        assess_quality: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of academic paper

        Args:
            paper_data: Paper metadata and content
            extract_keywords: Whether to extract keywords
            generate_summary: Whether to generate summary
            analyze_citations: Whether to analyze citations
            assess_quality: Whether to assess paper quality

        Returns:
            Dictionary containing analysis results
        """
        try:
            analysis_result = {
                'paper_id': paper_data.get('arxiv_id') or paper_data.get('doi'),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_version': '1.0'
            }

            # Extract keywords
            if extract_keywords:
                analysis_result['keywords'] = await self._extract_keywords(paper_data)

            # Generate summary
            if generate_summary:
                analysis_result['summary'] = await self._generate_summary(paper_data)

            # Analyze citations
            if analyze_citations and paper_data.get('citations'):
                analysis_result['citation_analysis'] = await self._analyze_citations(paper_data)

            # Assess quality
            if assess_quality:
                analysis_result['quality_assessment'] = await self._assess_paper_quality(paper_data)

            # Extract key insights
            analysis_result['key_insights'] = await self._extract_key_insights(paper_data)

            return analysis_result

        except Exception as e:
            self.logger.error(f"Error analyzing paper: {e}")
            return {
                'paper_id': paper_data.get('arxiv_id') or paper_data.get('doi'),
                'analysis_timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    async def _extract_keywords(self, paper_data: Dict[str, Any]) -> List[str]:
        """
        Extract keywords from paper content using LLM

        Args:
            paper_data: Paper metadata and content

        Returns:
            List of extracted keywords
        """
        try:
            # Prepare content for keyword extraction
            content = self._prepare_content_for_analysis(paper_data)

            if not content:
                return []

            prompt = f"""
            Extract {self.settings.keyword_extraction_count} most important keywords from this academic paper.
            Focus on technical terms, methodologies, and key concepts.
            Return only the keywords as a comma-separated list, without numbering or additional text.

            Paper title: {paper_data.get('title', '')}

            Content:
            {content[:3000]}  # Limit content length for efficiency

            Keywords:
            """

            response = await self.llm_service.generate_text(
                prompt=prompt,
                max_tokens=200,
                temperature=0.3
            )

            # Parse keywords from response
            keywords = self._parse_keywords_from_response(response)

            self.logger.info(f"Extracted {len(keywords)} keywords")
            return keywords

        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []

    async def _generate_summary(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive summary of the paper

        Args:
            paper_data: Paper metadata and content

        Returns:
            Dictionary containing summary information
        """
        try:
            content = self._prepare_content_for_analysis(paper_data)

            if not content:
                return {'error': 'No content available for summarization'}

            prompt = f"""
            Generate a comprehensive summary of this academic paper in {self.settings.max_summary_length} words or less.
            Include:
            1. Main research question/problem
            2. Methodology used
            3. Key findings/results
            4. Significance/contributions
            5. Limitations (if any)

            Paper title: {paper_data.get('title', '')}
            Authors: {', '.join([author.get('name', '') for author in paper_data.get('authors', [])])}

            Content:
            {content[:4000]}  # Limit content length for efficiency

            Summary:
            """

            summary = await self.llm_service.generate_text(
                prompt=prompt,
                max_tokens=800,
                temperature=0.4
            )

            return {
                'summary_text': summary.strip(),
                'word_count': len(summary.split()),
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return {'error': str(e)}

    async def _analyze_citations(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze citations in the paper

        Args:
            paper_data: Paper metadata and content

        Returns:
            Dictionary containing citation analysis
        """
        try:
            citations = paper_data.get('citations', [])

            if not citations:
                return {'message': 'No citations found'}

            # Count citations
            citation_count = len(citations)

            # Analyze citation patterns
            citation_years = []
            citation_types = []

            for citation in citations:
                # Extract year if available
                if citation.get('date'):
                    try:
                        year = int(citation['date'][:4])
                        citation_years.append(year)
                    except (ValueError, TypeError):
                        pass

                # Extract type if available
                if citation.get('type'):
                    citation_types.append(citation['type'])

            # Calculate statistics
            analysis = {
                'total_citations': citation_count,
                'citation_years': citation_years,
                'citation_types': citation_types,
                'average_citation_year': sum(citation_years) / len(citation_years) if citation_years else None,
                'oldest_citation_year': min(citation_years) if citation_years else None,
                'newest_citation_year': max(citation_years) if citation_years else None
            }

            # Generate citation insights using LLM
            if citations:
                citation_text = "\n".join([
                    f"- {citation.get('title', 'Unknown')} ({citation.get('date', 'Unknown date')})"
                    for citation in citations[:20]  # Limit for efficiency
                ])

                prompt = f"""
                Analyze the citation patterns in this academic paper and provide insights about:
                1. The types of sources being cited
                2. The temporal distribution of citations
                3. The relevance and quality of cited works
                4. Any notable trends or patterns

                Paper title: {paper_data.get('title', '')}

                Citations:
                {citation_text}

                Analysis:
                """

                citation_insights = await self.llm_service.generate_text(
                    prompt=prompt,
                    max_tokens=400,
                    temperature=0.5
                )

                analysis['insights'] = citation_insights.strip()

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing citations: {e}")
            return {'error': str(e)}

    async def _assess_paper_quality(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the quality of the academic paper

        Args:
            paper_data: Paper metadata and content

        Returns:
            Dictionary containing quality assessment
        """
        try:
            content = self._prepare_content_for_analysis(paper_data)

            if not content:
                return {'error': 'No content available for quality assessment'}

            prompt = f"""
            Assess the quality of this academic paper on a scale of 1-10 and provide detailed feedback.
            Consider:
            1. Clarity of research question
            2. Methodology rigor
            3. Data quality and analysis
            4. Writing quality and structure
            5. Significance of findings
            6. Limitations and future work

            Paper title: {paper_data.get('title', '')}
            Authors: {', '.join([author.get('name', '') for author in paper_data.get('authors', [])])}

            Content:
            {content[:3000]}

            Quality Assessment (1-10):
            """

            quality_assessment = await self.llm_service.generate_text(
                prompt=prompt,
                max_tokens=600,
                temperature=0.3
            )

            # Extract numerical score if present
            score_match = re.search(r'(\d+(?:\.\d+)?)/10', quality_assessment)
            score = float(score_match.group(1)) if score_match else None

            return {
                'score': score,
                'assessment_text': quality_assessment.strip(),
                'assessed_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error assessing paper quality: {e}")
            return {'error': str(e)}

    async def _extract_key_insights(self, paper_data: Dict[str, Any]) -> List[str]:
        """
        Extract key insights from the paper

        Args:
            paper_data: Paper metadata and content

        Returns:
            List of key insights
        """
        try:
            content = self._prepare_content_for_analysis(paper_data)

            if not content:
                return []

            prompt = f"""
            Extract 5-7 key insights from this academic paper.
            Focus on:
            1. Novel findings or contributions
            2. Important implications
            3. Key methodologies or approaches
            4. Significant results
            5. Future research directions

            Paper title: {paper_data.get('title', '')}

            Content:
            {content[:3000]}

            Key Insights:
            1.
            """

            insights_response = await self.llm_service.generate_text(
                prompt=prompt,
                max_tokens=500,
                temperature=0.4
            )

            # Parse numbered insights
            insights = self._parse_numbered_list(insights_response)

            return insights

        except Exception as e:
            self.logger.error(f"Error extracting key insights: {e}")
            return []

    def _prepare_content_for_analysis(self, paper_data: Dict[str, Any]) -> str:
        """
        Prepare content for LLM analysis

        Args:
            paper_data: Paper metadata and content

        Returns:
            Prepared content string
        """
        content_parts = []

        # Add title
        if paper_data.get('title'):
            content_parts.append(f"Title: {paper_data['title']}")

        # Add abstract
        if paper_data.get('summary') or paper_data.get('abstract'):
            abstract = paper_data.get('summary') or paper_data.get('abstract')
            content_parts.append(f"Abstract: {abstract}")

        # Add body text
        if paper_data.get('body_text'):
            content_parts.append(f"Content: {paper_data['body_text']}")

        # Add extracted text from Grobid
        if paper_data.get('grobid_extraction', {}).get('body_text'):
            content_parts.append(f"Extracted Text: {paper_data['grobid_extraction']['body_text']}")

        return "\n\n".join(content_parts)

    def _parse_keywords_from_response(self, response: str) -> List[str]:
        """
        Parse keywords from LLM response

        Args:
            response: LLM response text

        Returns:
            List of keywords
        """
        try:
            # Clean up response
            response = response.strip()

            # Split by common delimiters
            keywords = []
            for delimiter in [',', ';', '\n']:
                if delimiter in response:
                    keywords = [kw.strip() for kw in response.split(delimiter) if kw.strip()]
                    break

            # If no delimiters found, try to extract individual words
            if not keywords:
                keywords = [word.strip() for word in response.split() if len(word.strip()) > 2]

            # Remove common stop words and clean up
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
            keywords = [kw for kw in keywords if kw.lower() not in stop_words and len(kw) > 2]

            return keywords[:self.settings.keyword_extraction_count]

        except Exception as e:
            self.logger.error(f"Error parsing keywords: {e}")
            return []

    def _parse_numbered_list(self, response: str) -> List[str]:
        """
        Parse numbered list from LLM response

        Args:
            response: LLM response text

        Returns:
            List of items
        """
        try:
            lines = response.strip().split('\n')
            items = []

            for line in lines:
                line = line.strip()
                # Remove numbering patterns like "1.", "1)", "-", etc.
                line = re.sub(r'^\d+[\.\)]\s*', '', line)
                line = re.sub(r'^[-*]\s*', '', line)

                if line and len(line) > 10:  # Minimum length for meaningful insight
                    items.append(line)

            return items

        except Exception as e:
            self.logger.error(f"Error parsing numbered list: {e}")
            return []

    async def compare_papers(
        self,
        papers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare multiple papers and identify relationships

        Args:
            papers: List of paper data dictionaries

        Returns:
            Dictionary containing comparison results
        """
        try:
            if len(papers) < 2:
                return {'error': 'Need at least 2 papers for comparison'}

            # Prepare comparison content
            comparison_content = []
            for i, paper in enumerate(papers, 1):
                paper_info = f"Paper {i}:\n"
                paper_info += f"Title: {paper.get('title', 'Unknown')}\n"
                paper_info += f"Abstract: {paper.get('summary', paper.get('abstract', ''))}\n"
                comparison_content.append(paper_info)

            content = "\n\n".join(comparison_content)

            prompt = f"""
            Compare these {len(papers)} academic papers and provide insights about:
            1. Similarities in research questions or methodologies
            2. Differences in approaches or findings
            3. Potential relationships or dependencies
            4. Complementary aspects
            5. Overall research landscape

            Papers:
            {content}

            Comparison Analysis:
            """

            comparison = await self.llm_service.generate_text(
                prompt=prompt,
                max_tokens=800,
                temperature=0.4
            )

            return {
                'comparison_text': comparison.strip(),
                'papers_compared': len(papers),
                'compared_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error comparing papers: {e}")
            return {'error': str(e)}
