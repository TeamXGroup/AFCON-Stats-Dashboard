import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import json
import matplotlib
import squarify
from streamlit_lottie import st_lottie
import streamlit_shadcn_ui as ui
import random
import plotly.express as px
from pathlib import Path
from season_data import COMPETITION_DATASETS, SEASON_YEARS, competition_summary, format_goal_average, load_overview

   
st.set_page_config(page_title='AFCON DASHBOARD',
                   page_icon='⚽',
                   layout='wide',
                   initial_sidebar_state="expanded",)


def load_data(path: str):
    data = pd.read_csv(path)
    return data

APP_DIR = Path(__file__).resolve().parent


def reset_team_selection():
    # A team or comparison from the previous competition may not participate.
    st.session_state.pop('selected_team', None)
    st.session_state.pop('comparison_teams', None)

season_years_desc = sorted(SEASON_YEARS, reverse=True)

competition_year = st.sidebar.selectbox(
    'Select AFCON Competition',
    season_years_desc,
    index=season_years_desc.index(2025),
    key='competition_year',
    on_change=reset_team_selection,
)

squads_path, players_path = COMPETITION_DATASETS[competition_year]
squads_df = load_data(squads_path)
players_df = load_data(players_path)
overview_data = load_overview(competition_year)



# PLOTS FUNCTIONS :

def unavailable_chart(title, detail='Statistics unavailable for this edition', height=500):
    fig = go.Figure()
    fig.update_layout(
        title=title, title_x=0.3, width=600, height=height,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    fig.add_annotation(text=detail, xref='paper', yref='paper',
                       x=0.5, y=0.5, showarrow=False)
    st.plotly_chart(fig, use_container_width=True)


def goals():
    # Sample data (teams, goals scored, and goals conceded)
    teams = squads_df['Team'].tolist()
    goals_scored = squads_df['Goals'].tolist()
    goals_conceded = squads_df['Goals Against'].tolist()

    # Create traces for each team
    data = []
    for i in range(len(teams)):
        team = teams[i]
        scored = goals_scored[i]
        conceded = goals_conceded[i]
    
        # Create a bar for goals scored
        data.append(go.Bar(
            x=[team],
            y=[scored],
            name='Goals Scored' if i == 0 else None,  # Add legend entry only for the first team
            marker=dict(color='#158106'),
            hovertemplate=f'{team}<br>Goals Scored: {scored}<extra></extra>',
            showlegend=True if i == 0 else False,  # Show legend only for the first team
            width = 0.4,
        ))
    
        # Create a bar for goals conceded, placed above the green bar
        data.append(go.Bar(
            x=[team],
            y=[conceded],
            name='Goals Conceded' if i == 0 else None,  # Add legend entry only for the first team
            marker=dict(color='#FC8600'),
            base=[scored],  # Base set to the height of the green bar
            hovertemplate=f'{team}<br>Goals Conceded: {conceded}<extra></extra>',
            showlegend=True if i == 0 else False,  # Show legend only for the first team
            width = 0.4,
        ))

    # Create layout for the chart
    layout = go.Layout(
        title='Goals Scored vs Goals Conceded',
        title_x=0.3,
        title_y=0.9,
        barmode='relative',  # Stacked bar chart
        yaxis=dict(title='Goals', showgrid=False),
        xaxis=dict(title='Teams'),
        hovermode='closest',  # Show closest data on hover
        plot_bgcolor='rgba(0,0,0,0)',  # Set plot background color to transparent
        paper_bgcolor='rgba(0,0,0,0)',  # Set paper background color to transparent
        width = 600,
        height = 500,
    )

    # Create figure
    fig = go.Figure(data=data, layout=layout)

    # Show figure
    st.plotly_chart(fig, use_container_width=True)
def possession():
    # Sample data (teams and possessions)
    available = squads_df.dropna(subset=['Possession'])
    if available.empty:
        unavailable_chart('Possession by Team (Heatmap)')
        return
    teams = available['Team'].tolist()
    possession = available['Possession'].tolist()

    # Sort teams and possession in descending order of possession
    teams_sorted, possession_sorted = zip(*sorted(zip(teams, possession), key=lambda x: x[1], reverse=True))

    # Create a heatmap with the "YlOrRd" color scale
    fig = go.Figure(data=go.Heatmap(
        z=[possession_sorted],  # Sorted possession data
        x=teams_sorted,  # Sorted teams on the x-axis
        y=['Possession (%)'],  # Y-axis label
        colorscale='YlOrRd',  # YlOrRd color scale
        hovertemplate='%{x}<br>Possession: %{z}%<extra></extra>',  # Custom hover template
    ))

    # Update layout
    fig.update_layout(
        title='Possession by Team (Heatmap)',
        title_x=0.3,
        title_y=0.9,
        xaxis=dict(title='Team'),  # X-axis label
        hovermode='closest',  # Show closest data on hover
        width = 600,
        height = 500,
    )

    # Show figure
    st.plotly_chart(fig, use_container_width=True)
def goals_timing():
    timing = overview_data.get('goal_timing')
    if not timing:
        unavailable_chart('Goals Timing', f'Goal timing unavailable for AFCON {competition_year}')
        return
    segments = timing['segments']
    goals = timing['goals']
    percentages = timing['percentages']

    # Find the index of the maximum value in the goals list
    max_index = goals.index(max(goals))

    # Create a list of colors, setting the color of the largest segment to orange
    colors = ['#158106'] * len(goals)
    colors[max_index] = '#FC8600'  # Set the color of the largest segment to orange

    # Create a horizontal bar chart
    fig = go.Figure(go.Bar(
        y=segments,  # Segments on the y-axis
        x=goals,  # Number of goals on the x-axis
        orientation='h',  # Horizontal orientation
        marker=dict(color=colors),  # Bar color
        text=[f'{percentage}%' for percentage in percentages],  # Text within bars (percentages)
        hovertemplate='Number of Goals: %{x}<extra></extra>',  # Custom hover template (showing only number of goals)
        textfont=dict(size=14),  # Customize text size for percentages
    ))

    # Update layout
    fig.update_layout(
        title='Goals Timing',
        title_x=0.4,
        title_y=0.9,
        xaxis=dict(title='Number of Goals'),  # X-axis label
        yaxis=dict(title='Time Segments'),  # Y-axis label
        hovermode='closest',  # Show closest data on hover
        plot_bgcolor='rgba(0,0,0,0)',  # Set plot background color to transparent
        paper_bgcolor='rgba(0,0,0,0)',  # Set paper background color to transparent
        width = 600,
        height = 500,
    )

    # Show figure
    st.plotly_chart(fig, use_container_width=True)
def fouls_cards():
    available = squads_df.dropna(subset=['Fouls Commited', 'Yellow Cards', 'Red Cards'])
    if available.empty:
        unavailable_chart('Fouls Committed vs Total Cards')
        return
    teams = available['Team'].tolist()
    fouls_committed = available['Fouls Commited'].tolist()
    yellow_cards = available['Yellow Cards'].tolist()
    red_cards = available['Red Cards'].tolist()

    # Calculate total cards (yellow + red)
    total_cards = [yc + rc for yc, rc in zip(yellow_cards, red_cards)]


    # Create traces for fouls committed
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=teams,
        y=fouls_committed,
        name='Fouls Committed',
        marker_color='#158106',  # Bar color for fouls committed
    ))

    # Create traces for total cards received
    fig.add_trace(go.Scatter(
        x=teams,
        y=total_cards,
        name='Total Cards',
        mode='lines+markers',  # Line and marker mode for total cards
        yaxis='y2',  # Use secondary y-axis for total cards
        line=dict(color='#FF5733'),  # Line color for total cards
        marker=dict(color='#FF5733'),  # Marker color for total cards
    ))

    # Update layout
    fig.update_layout(
        title='Fouls Committed vs Total Cards',  # Title of the plot
        title_x=0.3,
        title_y=0.9,
        xaxis=dict(title='Team'),  # X-axis label
        yaxis=dict(title='Fouls Committed'),  # Y-axis label for fouls committed
        yaxis2=dict(title='Total Cards', overlaying='y', side='right'),  # Secondary y-axis label for total cards
        plot_bgcolor='rgba(0,0,0,0)',  # Set plot background color to transparent
        paper_bgcolor='rgba(0,0,0,0)',  # Set paper background color to transparent
        width = 600,
        height = 500,
    )   

    st.plotly_chart(fig, use_container_width=True)
def all_top_contributors():

    # Sort DataFrame based on "Goals+Assists" column and select top contributors
    top_contributors = players_df.sort_values(by="Goals\Assists", ascending=False).head(10)
    top_contributors = top_contributors[::-1]

    # Create horizontal lollipop chart with different colors for goals and assists
    fig = plt.figure(figsize=(6, 5))

    plt.hlines(y=top_contributors["Player"], xmin=0, xmax=top_contributors["Goals"], color='#158106', label='Goals', linewidth=3)
    plt.hlines(y=top_contributors["Player"], xmin=top_contributors["Goals"], xmax=top_contributors["Goals\Assists"], color='#FF5733', label='Assists', linewidth=3)
    # Add marker at the end
    plt.plot(top_contributors["Goals\Assists"], top_contributors["Player"], 'o', color='blue', markersize=5)

    plt.xlabel('Goals + Assists')
    plt.ylabel('Players')
    plt.title('Top Contributors')
    plt.legend()

    plt.grid(axis='x', linestyle='--', alpha=0.7)

    plt.legend(loc='lower right', prop={'size': 10})

    plt.tight_layout()

    st.pyplot(fig)
def top_cls():

    # Sort DataFrame based on "Goals+Assists" column and select top contributors
    top_clean_sheets = squads_df.sort_values(by="Clean Sheets", ascending=False).head(10)
    top_clean_sheets = top_clean_sheets[::-1]

    # Create horizontal lollipop chart with different colors for goals and assists
    fig = plt.figure(figsize=(6, 5))

    plt.hlines(y=top_clean_sheets["Team"], xmin=0, xmax=top_clean_sheets["Clean Sheets"], color='#158106', label='Clean Sheets', linewidth=3)

    # Add marker at the end
    plt.plot(top_clean_sheets["Clean Sheets"], top_clean_sheets["Team"], 'o', color='blue', markersize=5)

    plt.xlabel('Clean Sheets')
    plt.ylabel('Team')
    plt.title('Top Clean Sheets')
    plt.legend()

    plt.grid(axis='x', linestyle='--', alpha=0.7)

    plt.legend(loc='lower right', prop={'size': 10})

    plt.tight_layout()

    st.pyplot(fig)
def all_goals_type():
    # Calculate total goals for each type
    total_penalty_goals = squads_df["Penalty Goals"].sum()
    total_non_penalty_goals = squads_df["Non-Penalty Goals"].sum()
    total_own_goals = squads_df["Own Goals"].sum()

    # Create labels and values for the pie chart
    labels = ['Penalty Goals', 'Non-Penalty Goals', 'Own Goals']
    values = [total_penalty_goals, total_non_penalty_goals, total_own_goals]


    # Define colors for each part
    colors = ['#FC8600', '#158106', '#5F8DF7']

    # Create the donut chart
    fig = go.Figure(data=[go.Pie(labels=labels, values=values,  
                                textinfo='value',
                                hovertemplate = '%{label}: %{percent}<extra></extra>',
                                hole=0.4,   # Set hole attribute to create a donut chart
                                marker=dict(colors=colors))])

    # Update layout
    fig.update_layout(
        title="Distribution of Goals",
        title_x=0.1,
        title_y=0.9,
        legend_title="Goal Type",
        width = 600,
        height = 500,
    )

    # Adjust the text size and color inside the pie chart
    fig.update_traces(textfont_size=16, insidetextfont=dict(size=25, color='white'))  # Change the text size to 16 and color to white

    # Show the plot
    st.plotly_chart(fig, use_container_width=True)
def players_top_minutes(selected_team):
    # New dataframe, containing only players with more than 0 goals.
    data = players_df[players_df['Team'] == selected_team].sort_values(by='Minutes', ascending=False).head(11)

    #Utilise matplotlib to scale our goal numbers between the min and max, then assign this scale to our values.
    norm = matplotlib.colors.Normalize(vmin=min(data['Minutes']), vmax=max(data['Minutes']))
    colors = [matplotlib.cm.summer_r(norm(value)) for value in data['Minutes']]

    #Create our plot and resize it.
    fig = plt.gcf()
    ax = fig.add_subplot()
    fig.set_size_inches(16, 5.5)

    # Combine player names and minutes for labels
    labels = [f"{player}\n\n{minutes} Mins" for player, minutes in zip(data['Player'], data['Minutes'])]

    #Use squarify to plot our data, label it and add colours. We add an alpha layer to ensure black labels show through
    squarify.plot(label=labels,sizes=data['Minutes'], color = colors, alpha=.6)
    plt.title(f"Top 11 Players Playing by Minutes in {selected_team}",fontsize=20,fontweight="bold")

    #Remove our axes and display the plot
    plt.axis('off')
    st.pyplot(fig)
def teams_goals_type(selected_team):
    # Filter data for the selected team
    team_data = squads_df[squads_df['Team'] == selected_team]

    # Calculate total goals for each type
    total_penalty_goals = team_data["Penalty Goals"].sum()
    total_non_penalty_goals = team_data["Non-Penalty Goals"].sum()
    total_own_goals = team_data["Own Goals"].sum()

    # Create labels and values for the pie chart
    labels = ['Penalty Goals', 'Non-Penalty Goals', 'Own Goals']
    values = [total_penalty_goals, total_non_penalty_goals, total_own_goals]


    # Define colors for each part
    colors = ['#FF5733', '#158106', '#5F8DF7']

    # Create the pie chart
    fig = go.Figure(data=[go.Pie(labels=labels, values=values,  
                                textinfo='value',
                                hovertemplate = '%{label}: %{percent}<extra></extra>',
                                hole=0.4,   # Set hole attribute to create a donut chart
                                marker=dict(colors=colors))])

    # Update layout
    fig.update_layout(
        title=f"Distribution of Goals for {selected_team}",
        title_y=0.9,
        legend_title="Goal Type",
        width = 600,
        height = 500,
    )

    # Adjust the text size and color inside the pie chart
    fig.update_traces(textfont_size=16, insidetextfont=dict(size=25, color='white'))  # Change the text size to 16 and color to white

    # Show the plot
    st.plotly_chart(fig, use_container_width=True)
def radar_chart(selected_team, teams_to_display):
    metrics = ['Shots on Target %', 'Possession', 'Interceptions', 'Tackles Won', 'Saves%']

    selected_teams = [selected_team] + teams_to_display  # Include the selected team and the teams to display

    team_data = squads_df[squads_df['Team'].isin(selected_teams)]

    # Missing provider statistics are omitted, never displayed as zero.
    metrics = [metric for metric in metrics if team_data[metric].notna().all()]
    if not metrics:
        unavailable_chart('Radar Chart for Metrics Comparison')
        return

    data = []
    for team_name in selected_teams:
        team_data_selected = team_data[team_data['Team'] == team_name]
        r_values = team_data_selected[metrics].values.flatten().tolist()
        r_values.append(r_values[0])
        line_color = '#FF5733' if team_name == selected_team else '#{:06x}'.format(random.randint(0, 0xFFFFFF))
        
        # Create hover text with metric names and values
        hover_text = [f'{team_name} {metric}: {value}' for metric, value in zip(metrics, r_values[:-1])] + [f'{team_name} Shots on Target %: ' + str(r_values[0])]
        
        data.append(go.Scatterpolar(
            r=r_values,
            theta=metrics + [metrics[0]],  # Append the first metric to close the lines
            fill='toself',
            name=team_name,
            line=dict(color=line_color),
            hoverinfo='text',  # Show custom text on hover
            text=hover_text  # Set the hover text 
        ))

    layout = go.Layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, team_data[metrics].values.max()]
            )),
        showlegend=True,
        title=f'Radar Chart for Metrics Comparison',
        title_x=0.2,
        title_y=0.95,
        width = 600,
        height = 500,
    )

    fig = go.Figure(data=data, layout=layout)

    st.plotly_chart(fig, use_container_width=True)
def teams_top_tacklers(selected_team):
    players = players_df['Team'].tolist()
    tackles_won = players_df['Tackles Won'].tolist()
    

    # Filter data for the selected country
    selected_team_data = players_df[players_df["Team"] == selected_team].sort_values(by='Tackles Won', ascending=False).head(10)
    selected_team_data = selected_team_data.dropna(subset=['Tackles Won'])
    if selected_team_data.empty:
        unavailable_chart(f'Top 10 Players by Tackles Won in {selected_team}')
        return

    # Create a scatter plot
    fig = px.scatter(selected_team_data, x='Player', y='Tackles Won', color='Tackles Won',
                     title=f'Top 10 Players by Tackles Won in {selected_team}', color_continuous_scale='Bluered')


    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    fig.update_layout(plot_bgcolor='#FDFDFD', title_x=0.3, title_y=0.9)  

    # Change the size of points
    fig.update_traces(marker=dict(size=12))  # Set the size of points to 10 pixels

    # Show the plot
    st.plotly_chart(fig, use_container_width=True)
def shots_on_target():

    # Sort the teams by shots on target % and select the top 10 teams
    teams = squads_df.dropna(subset=['Shots on Target %']).sort_values(by='Shots on Target %', ascending=False)
    if teams.empty:
        unavailable_chart('Shots on Target % by Team')
        return

    # Create a scatter plot
    fig = px.scatter(teams, x='Team', y='Shots on Target %', color='Shots on Target %',
                     title="Shots on Target % by Team", color_continuous_scale='Bluered')

    # Update axes and layout
    fig.update_xaxes(showgrid=True, title='Team')
    fig.update_yaxes(showgrid=True, title='Shots on Target %')
    fig.update_layout(plot_bgcolor='#FDFDFD',title_x=0.3, title_y=0.9)  # Set width and height

    # Change the size of points
    fig.update_traces(marker=dict(size=12))  # Set the size of points to 10 pixels

    # Show the plot
    st.plotly_chart(fig, use_container_width=True)
def team_cards(selected_team):
    # Filter data for the selected team
    team_data = squads_df[squads_df['Team'] == selected_team]

    # Create traces for goals and assists for each player
    data = []
        
    # Create a horizontal bar for goals
    data.append(go.Bar(
        x=team_data['Red Cards'],
        y=team_data['Team'],
        name='Red Cards',
        marker=dict(color='#C70039'),
        orientation='h',  # Horizontal bar
        hovertemplate='%{y}: %{x} Red Cards<extra></extra>', 
        width=0.4,
    ))
        
    # Create a horizontal bar for assists
    data.append(go.Bar(
        x=team_data['Yellow Cards'],
        y=team_data['Team'],
        name='Yellow Cards',
        marker=dict(color='#EEE700'),
        orientation='h',  # Horizontal bar
        hovertemplate='%{y}: %{x} Yellow Cards<extra></extra>', 
        width=0.4,
    ))

    # Create layout for the chart
    layout = go.Layout(
        title=f'Cards Distribution against {selected_team}',
        title_x=0.3,
        title_y=0.9,
        barmode='relative',  # Stacked bar chart
        xaxis=dict(title='Cards', showgrid=False),  # Adjusted x-axis
        yaxis=dict(title=f'{selected_team}', showticklabels=False),
        hovermode='closest',  # Show closest data on hover
        plot_bgcolor='rgba(0,0,0,0)',  # Set plot background color to transparent
        paper_bgcolor='rgba(0,0,0,0)',  # Set paper background color to transparent
        width=600,
        height=220,
        legend=dict(
            x=1.0,  # Adjust x position of the legend
            y=2, 
        ),
    )
    

    # Create figure
    fig = go.Figure(data=data, layout=layout)
    # Show figure
    st.plotly_chart(fig, use_container_width=True)
def teams_top_contributors(selected_team):
    # Filter data for the selected team
    team_data = players_df[players_df['Team'] == selected_team]

    # Filter out players with zero contributions
    team_data = team_data[(team_data['Goals'] > 0) | (team_data['Assists'] > 0)]

    # Calculate total contributions (goals + assists)
    team_data['Total Contributions'] = team_data['Goals'] + team_data['Assists']

    # Sort players based on total contributions in decreasing order
    team_data = team_data.sort_values(by='Total Contributions', ascending=False)

    # Get the top 10 contributors by total contributions in the selected team
    top_10_players = team_data.head(10)
    #top_10_players = top_10_players[::-1]

    # Create traces for goals and assists for each player
    data = []
    for i in range(len(top_10_players)):
        player = top_10_players.iloc[i]['Player']
        player_goals = top_10_players.iloc[i]['Goals']
        player_assists = top_10_players.iloc[i]['Assists']
        
        # Create a vertical bar for goals
        data.append(go.Bar(
            x=[player],
            y=[player_goals],
            name='Goals',
            marker=dict(color='#158106'),
            orientation='v',  # Vertical bar
            hovertemplate=f'{player}<br>Goals: {player_goals}<extra></extra>',
            showlegend=True if i == 0 else False,  # Show legend only for the first player
            width=0.4,
        ))
        
        # Create a vertical bar for assists
        data.append(go.Bar(
            x=[player],
            y=[player_assists],
            name='Assists',
            marker=dict(color='#FF5733'),
            orientation='v',  # Vertical bar
            hovertemplate=f'{player}<br>Assists: {player_assists}<extra></extra>',
            showlegend=True if i == 0 else False,  # Show legend only for the first player
            width=0.4,
        ))

    # Create layout for the chart
    layout = go.Layout(
        title=f'Top Contributors for {selected_team}',
        title_x=0.3,
        title_y=0.9,
        barmode='relative',  # Stacked bar chart
        xaxis=dict(title='Players'),  # Adjusted x-axis
        yaxis=dict(title='Contributions', showgrid=False),
        hovermode='closest',  # Show closest data on hover
        plot_bgcolor='rgba(0,0,0,0)',  # Set plot background color to transparent
        paper_bgcolor='rgba(0,0,0,0)',  # Set paper background color to transparent
        width=600,
        height=500,
    )

    # Create figure
    fig = go.Figure(data=data, layout=layout)

    # Show figure
    st.plotly_chart(fig, use_container_width=True)



def main():

    afcon_png = overview_data.get('logo_url')
    if afcon_png:
        historical_logo = competition_year <= 2021

        if historical_logo:
            img_width = 180 if competition_year == 2021 else 150

            _, col, _ = st.sidebar.columns([1, 3, 1])

            with col:
                st.image(
                    afcon_png,
                    width=img_width,
                    output_format='auto'
                )
        else:
            st.sidebar.image(
                afcon_png,
                width=100,
                use_column_width=True,
                output_format='auto'
            )
    else:
        st.sidebar.markdown(f'⚽ **AFCON {competition_year}**')

    def load_lottieurl(url: str):
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()              

    page = st.sidebar.radio('Go to', ['Overview', 'By Team'])
    
    if page == 'Overview':

        col1, col2 = st.columns((1,8))
        with col1:
            lottie_animation = load_lottieurl("https://lottie.host/7eff8345-9933-4bde-b787-2256aa370845/6nG4melsvc.json")
            st_lottie(lottie_animation, loop=False, height=100, width=100)
        with col2:
            st.markdown(f"<h1><span style='color:#158106; font-size:40px; font-family:Arial, sans-serif'>AFCON</span><span style='color:#FC8600; font-size:40px; font-family:Arial, sans-serif'>{str(competition_year)[-2:]}</span> Overview</h1>", unsafe_allow_html=True)
        
        for i in range(4):
            st.sidebar.write("##")
        st.sidebar.write("© Developed By TEAMX")

        col1, col2, col3 = st.columns(3)
        with col1:
            ui.metric_card(title="Teams", content=str(len(squads_df)))
        with col2:
            ui.metric_card(title="Matches Played", content=str(int(squads_df['Matches Played'].sum() / 2)))
        with col3:
            ui.metric_card(title="Players Participated", content="605" if competition_year == 2023 else str(len(players_df)))
        

        goals()
        col1, col2 = st.columns(2)
        with col1:
            goals_timing()
        with col2:
            all_goals_type()
        possession()
        shots_on_target()

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        if competition_year == 2023:
            col1.metric(label = "_**Goals per match**_", value = "2.29", delta = "+ 0.37 from Last Competition")
            col2.metric("_**Attendance Per Game**_", "27,223", "+ 4,337 from Last Competition")
            col3.metric("_**Total Revenue (estimated)**_", "$74.75 million", "- $4.95 million from Last Competition")
        else:
            summary = competition_summary(competition_year, squads_df)
            position = SEASON_YEARS.index(competition_year)
            previous_year = SEASON_YEARS[position - 1] if position else None
            previous = competition_summary(previous_year) if previous_year else {}

            def change(field, money=False, digits=2):
                current, earlier = summary[field], previous.get(field)
                if current is None or earlier is None:
                    return None
                difference = current - earlier
                if money:
                    return f"{'+' if difference >= 0 else '-'} ${abs(difference):.2f} million from {previous_year}"
                value = f'{difference:+,.0f}' if digits == 0 else f'{difference:+.2f}'
                return f'{value} from {previous_year}'

            col1.metric("_**Goals per match**_", format_goal_average(summary['goals_per_match']),
                        change('goals_per_match'))
            attendance = summary['attendance']
            col2.metric("_**Attendance Per Game**_", 'N/A' if attendance is None else f'{attendance:,.0f}',
                        change('attendance', digits=0))
            revenue = summary['revenue']
            revenue_label = 'Total Revenue (estimated)' if overview_data['revenue'].get('estimated') else 'Total Revenue'
            col3.metric(f'_**{revenue_label}**_', 'N/A' if revenue is None else f'${revenue:.2f} million',
                        change('revenue', money=True))

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            all_top_contributors()
        with col2:    
            top_cls()
        fouls_cards()



    elif page == 'By Team':

        
        # Display a select box in the sidebar for choosing a team
        selected_team = st.sidebar.selectbox(
            'Select a Team',
            squads_df['Team'],
            key='selected_team',
        )

        col1, col2 = st.columns((1,7))
        with col1:
            lottie_animation = load_lottieurl("https://lottie.host/43f17999-7769-4c96-8ea8-69143d28fbaa/ttQyXYQwpc.json")
            st_lottie(lottie_animation, loop=False, height=100, width=100, speed=2)
        with col2:
            st.markdown(f"<h1><span style='color:#FC8600; font-size:40px; font-family:Arial, sans-serif'>{selected_team}</span> Stats</h1>", unsafe_allow_html=True)
        
        # Display the flag of the selected team
        if selected_team:
            selected_flag_url = squads_df[squads_df['Team'] == selected_team]['Flags'].iloc[0]
            st.sidebar.image(selected_flag_url, width=100, use_column_width=True, output_format='auto')
            selected_row = squads_df[squads_df['Team'] == selected_team]
            st.sidebar.write("")
            st.sidebar.write(f"<b> Participations:</b> <b>{selected_row['Participations'].iloc[0]}<b>", unsafe_allow_html=True)
            # Get the value of Times_Won
            times_won = selected_row['Times_Won'].iloc[0]
            if times_won == 0:
                stars = '0'
            # Create a string with star emojis
            else:
                stars = '⭐' * times_won
            st.sidebar.write(f"<b>Times Won:</b> <b>{stars}</b>", unsafe_allow_html=True)
            for i in range(3): 
                st.sidebar.write("##")
            st.sidebar.write("©Developed By TEAMX")

            col1, col2, col3 = st.columns(3)
            #team_data = squads_df[squads_df['Team'] == selected_team]
            with col1:
                ui.metric_card(title="Number of players", content=f"{selected_row['Number of Players'].values[0]}")
            with col2:
                ui.metric_card(title="Average Age", content=f"{selected_row['Averagae Age'].values[0]}")
            with col3:
                ui.metric_card(title="Matches Played", content=f"{selected_row['Matches Played'].values[0]}") 
        
        st.write("##")
        players_top_minutes(selected_team)
        col1, col2 = st.columns((2, 1))
        with col1:
            teams_top_contributors(selected_team)
        with col2:
            teams_goals_type(selected_team)
        
        teams_top_tacklers(selected_team)
        team_cards(selected_team)

        
        st.markdown("---")
        col1,col2 = st.columns((3, 1))
        with col2:
            teams = squads_df['Team'].unique()
            teams_to_display = st.multiselect('Select Teams to Compare:', [team for team in teams if team != selected_team], key='comparison_teams')
        with col1:
            radar_chart(selected_team, teams_to_display)


if __name__ == "__main__":

    main()








#JUST FOR 700 LINES OF CODE 😁
